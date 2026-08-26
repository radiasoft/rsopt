"""Tests for the Py-BOBYQA persistent generator.

These drive the generator directly with a stand-in for libEnsemble's PersistentSupport so the
concurrency and routing logic can be exercised without starting an ensemble. Results are handed
back out of order and in partial batches, which is how they arrive from asynchronous workers.
"""
import numpy as np
import pytest

from libensemble.message_numbers import EVAL_GEN_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG
from rsopt.libe_tools.generator_functions import persistent_pybobyqa as gen_module
from rsopt.libe_tools.generator_functions.persistent_pybobyqa import persistent_pybobyqa

pybobyqa = pytest.importorskip('pybobyqa')

DIM = 2
H_DTYPE = np.dtype([('x', float, DIM), ('instance', int), ('f', float), ('sim_id', int),
                    ('given_back', bool)])


def quadratic(x):
    return float((x[0] - 0.3) ** 2 + (x[1] - 0.62) ** 2)


def rastrigin(x):
    z = np.asarray(x) * 10.24 - 5.12
    return float(20 + np.sum(z ** 2 - 10 * np.cos(2 * np.pi * z)))


class FakePersistentSupport:
    """Stands in for libEnsemble: assigns sim_ids, evaluates points, returns results out of order.

    `batch_limit` returns only part of what is outstanding, leaving the rest for a later recv, so
    points stay in flight across generator iterations the way they do with asynchronous workers.
    Which outstanding points complete is chosen at random (seeded) so that no instance is
    systematically starved, and each returned batch is ordered newest sim_id first so that results
    always arrive out of order.
    """

    def __init__(self, objective, sim_max, batch_limit=None, nan_at=(), seed=0):
        self.objective = objective
        self.sim_max = sim_max
        self.batch_limit = batch_limit
        self.nan_at = set(nan_at)
        self.rng = np.random.default_rng(seed)

        self.next_sim_id = 0
        self.outstanding = []  # (sim_id, x, f)
        self.evaluated = []  # (sim_id, x, f)
        self.max_in_flight = 0
        self.sends = []

    def __call__(self, libE_info, tag):
        return self

    def send(self, points):
        self.sends.append(len(points))
        for row in points:
            sim_id = self.next_sim_id
            self.next_sim_id += 1
            f = np.nan if sim_id in self.nan_at else self.objective(row['x'])
            self.outstanding.append((sim_id, np.array(row['x'], copy=True), f))
        self.max_in_flight = max(self.max_in_flight, len(self.outstanding))

    def recv(self):
        if len(self.evaluated) >= self.sim_max or not self.outstanding:
            return PERSIS_STOP, None, None

        selected = self.rng.permutation(len(self.outstanding))
        if self.batch_limit is not None:
            selected = selected[:self.batch_limit]
        returning = sorted((self.outstanding[i] for i in selected),
                           key=lambda r: r[0], reverse=True)

        for item in returning:
            self.outstanding.remove(item)
        self.evaluated.extend(returning)

        calc_in = np.zeros(len(returning), dtype=H_DTYPE)
        for i, (sim_id, x, f) in enumerate(returning):
            calc_in['sim_id'][i] = sim_id
            calc_in['x'][i] = x
            calc_in['f'][i] = f

        work = {'libE_info': {'H_rows': np.array([r[0] for r in returning])}}

        return EVAL_GEN_TAG, work, calc_in


def run_generator(monkeypatch, support, instances=1, xstart=(0.3, 0.7), **user):
    monkeypatch.setattr(gen_module, 'PersistentSupport', support)

    user_specs = {'lb': np.zeros(DIM), 'ub': np.ones(DIM), 'dim': DIM,
                  'xstart': np.array(xstart), 'instances': instances}
    user_specs.update(user)

    gen_specs = {'out': [('x', float, DIM), ('instance', int)], 'user': user_specs}
    persis_info = {'rand_stream': np.random.default_rng(0)}
    H = np.zeros(0, dtype=H_DTYPE)

    return persistent_pybobyqa(H, persis_info, gen_specs, {'comm': None})


def test_single_instance_finds_minimum(monkeypatch):
    support = FakePersistentSupport(quadratic, sim_max=80)
    local_H, persis_info, tag = run_generator(monkeypatch, support)

    assert tag == FINISHED_PERSISTENT_GEN_TAG
    assert support.max_in_flight == 1, 'a single instance must never have more than one point out'

    best = min(f for _, _, f in support.evaluated)
    assert best < 1e-8, f'expected convergence to the minimum, best f was {best}'


def test_first_point_is_the_start_point(monkeypatch):
    support = FakePersistentSupport(quadratic, sim_max=20)
    run_generator(monkeypatch, support, xstart=(0.11, 0.83))

    # the first point sent is always sim_id 0, and Py-BOBYQA always evaluates its start point first
    sim_zero = [x for sid, x, _ in support.evaluated if sid == 0][0]
    assert np.array_equal(sim_zero, np.array([0.11, 0.83]))


def test_multiple_instances_run_concurrently(monkeypatch):
    instances = 3
    support = FakePersistentSupport(rastrigin, sim_max=150, batch_limit=2)
    local_H, persis_info, tag = run_generator(monkeypatch, support, instances=instances,
                                              seek_global_minimum=True)

    assert tag == FINISHED_PERSISTENT_GEN_TAG
    assert support.sends[0] == instances, 'every instance should be given a point up front'
    assert support.max_in_flight == instances, \
        f'expected {instances} points in flight, saw {support.max_in_flight}'

    by_sim_id = sorted(support.evaluated, key=lambda r: r[0])
    starts = np.array([x for _, x, _ in by_sim_id[:instances]])
    assert len({tuple(s) for s in starts}) == instances, 'instances must start from distinct points'


def test_partial_batches_keep_points_in_flight(monkeypatch):
    """With only one result returned at a time the other instances stay busy."""
    support = FakePersistentSupport(rastrigin, sim_max=60, batch_limit=1)
    _, _, tag = run_generator(monkeypatch, support, instances=3, seek_global_minimum=True)

    assert tag == FINISHED_PERSISTENT_GEN_TAG
    assert support.max_in_flight == 3


def test_non_finite_objective_does_not_kill_instance(monkeypatch):
    """A NaN is fatal to Py-BOBYQA's model, so the generator substitutes a penalty instead."""
    support = FakePersistentSupport(quadratic, sim_max=80, nan_at=(6, 7, 8))
    _, _, tag = run_generator(monkeypatch, support)

    assert tag == FINISHED_PERSISTENT_GEN_TAG
    assert len(support.evaluated) >= 60, 'instance should have kept running past the NaN results'


def test_converged_instance_is_relaunched(monkeypatch):
    """A smooth problem converges well inside the budget; the worker must not then go idle."""
    support = FakePersistentSupport(quadratic, sim_max=120)
    _, persis_info, tag = run_generator(monkeypatch, support, restart_on_convergence=True)

    assert tag == FINISHED_PERSISTENT_GEN_TAG
    assert persis_info['pybobyqa_solutions'], 'expected at least one completed run'
    assert all(s['flag'] >= 0 for s in persis_info['pybobyqa_solutions'])
    assert len(support.evaluated) >= 120, 'generator should keep supplying points after convergence'


def test_retired_instance_ends_the_run(monkeypatch):
    """With restarts off, the generator finishes once every instance has converged."""
    support = FakePersistentSupport(quadratic, sim_max=500)
    _, persis_info, tag = run_generator(monkeypatch, support, restart_on_convergence=False)

    assert tag == FINISHED_PERSISTENT_GEN_TAG
    assert len(support.evaluated) < 500, 'run should end on convergence, not on the budget'
    assert len(persis_info['pybobyqa_solutions']) == 1


def test_child_processes_are_cleaned_up(monkeypatch):
    import psutil
    me = psutil.Process()
    before = {c.pid for c in me.children(recursive=True)}

    support = FakePersistentSupport(rastrigin, sim_max=60)
    run_generator(monkeypatch, support, instances=2, seek_global_minimum=True)

    after = {c.pid for c in me.children(recursive=True) if c.is_running()}
    assert not (after - before), f'left running child processes: {after - before}'


@pytest.mark.parametrize('seek_global_minimum, maxfun', [(False, 500), (True, 120)])
def test_matches_a_direct_pybobyqa_run(monkeypatch, seek_global_minimum, maxfun):
    """A single-instance rsopt run must reproduce pybobyqa.solve() point for point.

    Py-BOBYQA is deterministic for a given start point, so routing the objective through the
    generator, a structured array and a child process must not perturb the search at all. Exact
    equality is asserted deliberately: anything short of it means a point was dropped, duplicated,
    reordered or altered on the way through.
    """
    x0 = np.array([0.11, 0.83])

    direct = []

    def record(x):
        direct.append(np.array(x, copy=True))
        return quadratic(x)

    pybobyqa.solve(record, x0, bounds=(np.zeros(DIM), np.ones(DIM)), maxfun=maxfun,
                   seek_global_minimum=seek_global_minimum, do_logging=False)

    support = FakePersistentSupport(quadratic, sim_max=5000)
    local_H, _, _ = run_generator(monkeypatch, support, xstart=tuple(x0),
                                  restart_on_convergence=False, maxfun=maxfun,
                                  seek_global_minimum=seek_global_minimum)

    through_rsopt = [x for _, x, _ in sorted(support.evaluated, key=lambda r: r[0])]

    assert len(through_rsopt) == len(direct), \
        f'rsopt evaluated {len(through_rsopt)} points, direct run evaluated {len(direct)}'
    assert np.array_equal(np.array(through_rsopt), np.array(direct))
    assert np.array_equal(local_H['x'][:len(direct)], np.array(direct))


def test_instance_is_recorded_in_history(monkeypatch):
    """Each point in the history records which Py-BOBYQA instance requested it."""
    instances = 3
    support = FakePersistentSupport(rastrigin, sim_max=90, batch_limit=2)
    local_H, _, _ = run_generator(monkeypatch, support, instances=instances,
                                  seek_global_minimum=True)

    assert set(local_H['instance']) == set(range(instances))
    # the first point of each instance is its start point, and starts must differ
    firsts = [local_H['x'][local_H['instance'] == i][0] for i in range(instances)]
    assert len({tuple(f) for f in firsts}) == instances

    counts = [int(np.sum(local_H['instance'] == i)) for i in range(instances)]
    assert min(counts) > 1, f'every instance should have produced several points, got {counts}'


def _first_points(local_H, instances):
    """Start point of every instance, in instance order."""
    return [local_H['x'][local_H['instance'] == i][0] for i in range(instances)]


def test_additional_starts_are_used_in_order(monkeypatch):
    """Given points are the start points of instances 1..n, in the order they were given."""
    instances = 3
    given = [[0.9, 0.1], [0.25, 0.75]]
    support = FakePersistentSupport(quadratic, sim_max=60, batch_limit=2)
    local_H, _, _ = run_generator(monkeypatch, support, instances=instances, xstart=(0.5, 0.5),
                                  additional_instance_starts=given)

    firsts = _first_points(local_H, instances)
    assert np.array_equal(firsts[0], np.array([0.5, 0.5])), 'instance 0 uses the parameter start'
    assert np.array_equal(firsts[1], np.array(given[0]))
    assert np.array_equal(firsts[2], np.array(given[1]))


def test_partial_additional_starts_are_filled_randomly(monkeypatch):
    """Instances beyond the given points fall back to random starts within the bounds."""
    instances = 4
    given = [[0.9, 0.1]]
    support = FakePersistentSupport(quadratic, sim_max=80, batch_limit=2)
    local_H, _, _ = run_generator(monkeypatch, support, instances=instances, xstart=(0.5, 0.5),
                                  additional_instance_starts=given)

    firsts = _first_points(local_H, instances)
    assert np.array_equal(firsts[0], np.array([0.5, 0.5]))
    assert np.array_equal(firsts[1], np.array(given[0]))
    for point in firsts[2:]:
        assert np.all((point >= 0.0) & (point <= 1.0))
    assert len({tuple(f) for f in firsts}) == instances, 'random fills must not repeat a given start'


def test_additional_starts_are_not_reused_on_relaunch(monkeypatch):
    """A converged instance relaunches from a random point, not from the point it was given.

    Py-BOBYQA is deterministic in its start point, so reusing one would replay the same run.
    """
    instances = 2
    given = [[0.9, 0.1]]
    support = FakePersistentSupport(quadratic, sim_max=120, batch_limit=1)
    local_H, _, _ = run_generator(monkeypatch, support, instances=instances, xstart=(0.5, 0.5),
                                  additional_instance_starts=given, restart_on_convergence=True)

    starts = local_H['x'][local_H['instance'] == 1]
    repeats = np.sum(np.all(starts == np.array(given[0]), axis=1))
    assert repeats == 1, f'the given start point was evaluated {repeats} times, expected once'


def test_more_additional_starts_than_instances_are_ignored(monkeypatch):
    """The generator never starts more instances than it was asked for.

    Over-supply is rejected by PybobyqaOptimizer before the generator runs; this only pins down
    that the generator itself stays consistent if it is driven directly.
    """
    instances = 2
    given = [[0.9, 0.1], [0.25, 0.75], [0.4, 0.4]]
    support = FakePersistentSupport(quadratic, sim_max=40, batch_limit=2)
    local_H, _, _ = run_generator(monkeypatch, support, instances=instances, xstart=(0.5, 0.5),
                                  additional_instance_starts=given)

    assert set(local_H['instance']) == {0, 1}
    firsts = _first_points(local_H, instances)
    assert np.array_equal(firsts[1], np.array(given[0]))
