"""
Persistent generator running one or more concurrent Py-BOBYQA optimization instances.

Py-BOBYQA drives its own optimization loop and calls the objective function directly, so each
instance runs in a child process where the objective callback blocks on a queue until this
generator supplies a value obtained from libEnsemble. This is the mechanism libEnsemble's
`LocalOptInterfacer` uses for its local optimizers, reduced here to the only case Py-BOBYQA needs:
a scalar objective, no gradient, and real bounds (Py-BOBYQA rescales internally when
`scaling_within_bounds` is set, so no unit-cube transformation is performed here).

Instances are independent. Each starts from a different point and keeps its own trust region and
restart schedule, so `instances` simulation workers can be kept busy at once. Diversity between
instances comes from the starting points: Py-BOBYQA is deterministic for a given start unless
`init.random_initial_directions` is enabled through `user_params`, so each child is also given its
own random seed to cover that case.
"""
import logging
import numpy as np
import psutil
from multiprocessing import Event, Process, Queue

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG, EVAL_GEN_TAG
from libensemble.tools.persistent_support import PersistentSupport

logger = logging.getLogger('libensemble')
gen_log = logging.getLogger('gen-log')

# libEnsemble governs termination through exit_criteria. maxfun is only a stopping rule for
# Py-BOBYQA (it does not change which points are evaluated), so it is set high enough not to bind
# unless the user asks for a per-instance cap.
DEFAULT_MAX_EVALS = int(1e6)

# Substituted for a non-finite objective value, which is otherwise fatal to Py-BOBYQA's
# interpolation model. Kept equal to the penalty rsopt applies to failed jobs
# (`_PENALTY` in rsopt/simulation.py); not imported from there because `rsopt.simulation` cannot
# currently be imported as a first entry point (circular import through rsopt.codes).
_PENALTY = 1e9

# Keys in gen_specs['user'] that are passed straight through to pybobyqa.solve
_SOLVE_KEYS = ('npt', 'rhobeg', 'rhoend', 'maxfun', 'seek_global_minimum', 'objfun_has_noise',
               'scaling_within_bounds', 'user_params')


class PyBobyqaException(Exception):
    """Raised in the generator when a Py-BOBYQA child process fails."""


class ConvergedMsg:
    """Communicated by a child process when its Py-BOBYQA run has finished."""
    def __init__(self, x, f, flag, msg):
        self.x = x
        self.f = f
        self.flag = flag
        self.msg = msg


class ErrorMsg:
    """Communicated by a child process when its Py-BOBYQA run raised."""
    def __init__(self, x):
        self.x = x


def put_set_wait_get(x, comm_queue, parent_can_read, child_can_read):
    """Used by the child process objective callback. Puts `x` on the queue for the generator,
    waits for the generator to put back the matching (x, f) pair, and returns it.

    The x value is echoed back by the generator so that the child can verify it was given the
    objective value belonging to the point it asked for. With several instances running at once a
    mis-routed result would otherwise corrupt an instance's model silently.
    """
    comm_queue.put(x)
    parent_can_read.set()
    child_can_read.wait()
    values = comm_queue.get()
    child_can_read.clear()

    assert np.allclose(x, values[0], rtol=1e-15, atol=1e-15), \
        'Py-BOBYQA instance was given a result for a point it did not request'

    return values


def run_pybobyqa(user_specs, comm_queue, x0, child_can_read, parent_can_read, seed):
    """Child process target. Runs one Py-BOBYQA instance to completion, requesting each objective
    evaluation from the generator through `comm_queue`.
    """
    import pybobyqa

    # Only relevant if the user enables init.random_initial_directions through user_params;
    # Py-BOBYQA is deterministic otherwise. Without this every instance would make the same
    # random choices.
    np.random.seed(seed)

    lb = np.asarray(user_specs['lb'], dtype=float)
    ub = np.asarray(user_specs['ub'], dtype=float)

    solve_kwargs = {k: user_specs[k] for k in _SOLVE_KEYS if user_specs.get(k) is not None}
    solve_kwargs.setdefault('maxfun', DEFAULT_MAX_EVALS)

    def objective(x):
        _, f = put_set_wait_get(x, comm_queue, parent_can_read, child_can_read)
        return f

    soln = pybobyqa.solve(objective, x0, bounds=(lb, ub), do_logging=False, **solve_kwargs)

    comm_queue.put(ConvergedMsg(soln.x, soln.f, soln.flag, soln.msg))
    parent_can_read.set()


def opt_runner(user_specs, comm_queue, x0, child_can_read, parent_can_read, seed):
    try:
        run_pybobyqa(user_specs, comm_queue, x0, child_can_read, parent_can_read, seed)
    except Exception as e:
        comm_queue.put(ErrorMsg(e))
        parent_can_read.set()


class PyBobyqaRunner:
    """Owns one Py-BOBYQA child process and the handshake with it.

    After construction `next_x` holds the first point the instance wants evaluated, which is always
    exactly the starting point. Each subsequent point is obtained by passing the objective value of
    the previous one to `tell`.
    """

    def __init__(self, instance_id, x0, user_specs, seed):
        self.instance_id = instance_id
        self.x0 = np.asarray(x0, dtype=float)
        self.solution = None

        self.comm_queue = Queue()
        self.child_can_read = Event()
        self.parent_can_read = Event()
        self.parent_can_read.clear()

        self.process = Process(target=opt_runner,
                               args=(user_specs, self.comm_queue, self.x0,
                                     self.child_can_read, self.parent_can_read, seed))
        self.process.start()
        self.is_running = True

        self.parent_can_read.wait()
        x_new = self.comm_queue.get()
        if isinstance(x_new, ErrorMsg):
            raise PyBobyqaException(x_new.x)

        # Py-BOBYQA always evaluates the starting point first
        assert np.allclose(x_new, self.x0, rtol=1e-15, atol=1e-15), \
            'The first point requested by instance {} does not match its starting point'.format(instance_id)

        self.next_x = np.atleast_1d(x_new)

    def tell(self, x, f):
        """Give the instance the objective value for the point it last requested.

        Returns the next point to evaluate, or a `ConvergedMsg` if this instance has finished.
        """
        self.parent_can_read.clear()
        self.comm_queue.put((np.asarray(x, dtype=float), float(f)))
        self.child_can_read.set()
        self.parent_can_read.wait()

        x_new = self.comm_queue.get()
        if isinstance(x_new, ErrorMsg):
            raise PyBobyqaException(x_new.x)
        if isinstance(x_new, ConvergedMsg):
            self.solution = x_new
            self.next_x = None
            self.close()
            return x_new

        self.next_x = np.atleast_1d(x_new)
        return self.next_x

    def destroy(self):
        """Kill the child process and any of its children."""
        if self.process.is_alive():
            process = psutil.Process(self.process.pid)
            for child in process.children(recursive=True):
                child.kill()
            process.kill()
        self.close()

    def close(self):
        if not self.is_running:
            return
        self.process.join()
        self.comm_queue.close()
        self.comm_queue.join_thread()
        self.is_running = False


def start_points(xstart, lb, ub, n_instances, rand_stream):
    """First instance starts from the user's start point, the rest are drawn uniformly in bounds."""
    points = [np.asarray(xstart, dtype=float)]
    for _ in range(n_instances - 1):
        points.append(rand_stream.uniform(lb, ub))

    return points


def add_to_local_H(local_H, points, instance_ids, pending):
    """Append requested points to the local history and record which instance asked for each.

    The instance id is written into the history so that a run can be broken back down into the
    independent Py-BOBYQA runs that produced it.
    """
    len_local_H = len(local_H)
    num_pts = len(points)

    local_H.resize(len(local_H) + num_pts, refcheck=False)  # Adds num_pts rows of zeros to O
    local_H['x'][-num_pts:] = points
    local_H['instance'][-num_pts:] = instance_ids
    sim_ids = np.arange(len_local_H, len_local_H + num_pts)
    local_H['sim_id'][-num_pts:] = sim_ids

    for sim_id, instance_id in zip(sim_ids, instance_ids):
        pending[sim_id] = instance_id


def persistent_pybobyqa(H, persis_info, gen_specs, libE_info):
    """
    libEnsemble persistent generator running concurrent Py-BOBYQA instances.

    See: https://numericalalgorithmsgroup.github.io/pybobyqa
    """
    persistent = PersistentSupport(libE_info, EVAL_GEN_TAG)
    local_H = np.zeros(len(H), dtype=H.dtype)
    user_specs = gen_specs['user']

    lb = np.asarray(user_specs['lb'], dtype=float)
    ub = np.asarray(user_specs['ub'], dtype=float)
    n_instances = user_specs.get('instances') or 1
    restart_on_convergence = user_specs.get('restart_on_convergence', True)
    rand_stream = persis_info.get('rand_stream', np.random.default_rng())
    track_given_back = 'given_back' in (local_H.dtype.names or ())

    out_fields = [g[0] for g in gen_specs['out']]
    pending = {}  # sim_id -> instance_id
    solutions = []
    def launch(instance_id, x0):
        # The seed only matters if the user enables init.random_initial_directions through
        # user_params; drawing it from rand_stream inherits rsopt's options.seed semantics.
        return PyBobyqaRunner(instance_id, x0, user_specs, int(rand_stream.integers(0, 2 ** 31 - 1)))

    runners = {}
    try:
        # Start every instance and collect the first point from each
        points, instance_ids = [], []
        for instance_id, x0 in enumerate(start_points(user_specs['xstart'], lb, ub, n_instances, rand_stream)):
            runners[instance_id] = launch(instance_id, x0)
            points.append(runners[instance_id].next_x)
            instance_ids.append(instance_id)

        logger.info('Py-BOBYQA started {} instance(s)'.format(len(runners)))
        add_to_local_H(local_H, points, instance_ids, pending)
        persistent.send(local_H[-len(points):][out_fields])

        while True:
            tag, Work, calc_in = persistent.recv()
            if tag in [STOP_TAG, PERSIS_STOP]:
                break

            if track_given_back:
                local_H['given_back'][Work['libE_info']['H_rows']] = True

            points, instance_ids = [], []
            for row in calc_in:
                sim_id = row['sim_id']
                instance_id = pending.pop(sim_id)
                runner = runners.get(instance_id)
                if runner is None:
                    # Instance was retired while this point was still being evaluated
                    continue

                f = row['f']
                if not np.isfinite(f):
                    # A single non-finite value is fatal to Py-BOBYQA's interpolation model, so the
                    # same penalty rsopt applies to failed jobs is substituted here.
                    gen_log.debug('Instance {} received non-finite objective value; '
                                  'substituting penalty {}'.format(instance_id, _PENALTY))
                    f = _PENALTY

                x_new = runner.tell(local_H['x'][sim_id], f)

                if isinstance(x_new, ConvergedMsg):
                    solutions.append((instance_id, x_new))
                    logger.info('Py-BOBYQA instance {} finished with flag {} ({}) f={}'.format(
                        instance_id, x_new.flag, x_new.msg, x_new.f))
                    if x_new.flag < 0:
                        raise PyBobyqaException(
                            'Py-BOBYQA instance {} stopped with error flag {}: {}'.format(
                                instance_id, x_new.flag, x_new.msg))
                    runners.pop(instance_id)
                    if not restart_on_convergence:
                        continue
                    # Relaunch from a fresh start so the simulation worker does not go idle
                    runners[instance_id] = launch(instance_id, rand_stream.uniform(lb, ub))
                    x_new = runners[instance_id].next_x

                points.append(x_new)
                instance_ids.append(instance_id)

            if not runners:
                logger.info('All Py-BOBYQA instances have finished')
                break

            if points:
                add_to_local_H(local_H, points, instance_ids, pending)
                persistent.send(local_H[-len(points):][out_fields])

        persis_info['pybobyqa_solutions'] = [
            {'instance': i, 'x': s.x, 'f': s.f, 'flag': s.flag, 'msg': s.msg} for i, s in solutions
        ]

        return local_H, persis_info, FINISHED_PERSISTENT_GEN_TAG
    finally:
        for runner in runners.values():
            try:
                runner.destroy()
            except Exception:
                pass
