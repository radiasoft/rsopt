import numpy as np


from poap.controller import EvalRecord
from pySOT.experimental_design import SymmetricLatinHypercube
from pySOT.strategy import SRBFStrategy
from pySOT.surrogate import CubicKernel, LinearTail, RBFInterpolant
from pySOT.optimization_problems import OptimizationProblem

import logging
logger = logging.getLogger()

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG, EVAL_GEN_TAG
from libensemble.tools.persistent_support import PersistentSupport


class Problem(OptimizationProblem):
    def __init__(self, dim, lb, ub):
        self.dim = dim
        self.lb = lb
        self.ub = ub

        self.int_var = np.array([])
        self.cont_var = np.arange(0, dim)
        self.info = ''

    def eval(self, _):
        pass


def configure_pysot(problem, num_pts, max_evals):
    # pySOT Setup

    surrogate = RBFInterpolant(dim=problem.dim, lb=problem.lb, ub=problem.ub,
                               kernel=CubicKernel(), tail=LinearTail(problem.dim))
    exp_design = SymmetricLatinHypercube(dim=problem.dim, num_pts=num_pts)
    strategy = SRBFStrategy(
        max_evals=max_evals, opt_prob=problem, exp_design=exp_design, surrogate=surrogate, asynchronous=True
    )

    return strategy


def get_proposal(strategy):
    """Get a new action proposal from strategy and perform setup if it is an eval action. Will return action or None."""
    new_action = strategy.propose_action()
    if new_action:
        if new_action.action == 'eval':
            new_action.record = EvalRecord(new_action.args, extra_args=None, status='pending')
            # new_action.record.worker = 1
            new_action.accept()

    return new_action


def persistent_pysot(H, persis_info, gen_specs, libE_info):
    """
    Asynchronous evaluation with pySOT

    Notes:
     If a large number of experimental points (num_pts) are requested relative to max_evals
      (there is also a dependence on nworkers here) then pySOT may call
     for a termination before max_eval number of points are evaluated by libEnsemble. This is because pySOT
     preallocates num_pts for evaluation which are part of the max_eval budget. Once dim+1 points are evaluated though
     pySOT can start providing optimization points, even if there are still may experimental points left. This results
     in max_eval budget being reached without the full number of evaluations being carried out.
    :param H:
    :param persis_info:
    :param gen_specs:
    :param libE_info:
    :return:
    """

    # libEnsemble Setup
    persistent = PersistentSupport(libE_info, EVAL_GEN_TAG)

    libE_comm = libE_info['comm']

    dim = gen_specs['user']['dim']
    lb = gen_specs['user']['lb']
    ub = gen_specs['user']['ub']
    # pySOT causes problems terminating - setting max evals to always be larger by the thread count
    #  should guarantee that pySOT will run until libEnsemble stops the process
    max_evals = gen_specs['user']['max_evals']
    num_pts = gen_specs['user'].get('num_pts') or 2 * (dim + 1)
    assert max_evals >= num_pts, f"Number of initial evaluation points: num_pts={num_pts} is inconsistent " \
                                 f"with maximum allowed evaluations: max_evals={max_evals}"

    problem = Problem(dim, lb, ub)

    # Start pySOT
    pysot = configure_pysot(problem, num_pts, max_evals)
    surrogate_tail_dim = pysot.surrogate.ntail

    assert surrogate_tail_dim <= num_pts, f"Insufficient initial points to construct surrogate. " \
                                          f"Set num_pts > {surrogate_tail_dim}"

    try:
        # Initialize Worker communication and Begin
        local_H = np.zeros(len(H), dtype=H.dtype)
        proposals = []  # Entries are proposals from Strategy

        for _ in range(num_pts):
            # We do not check for terminations during the first round
            new_action = get_proposal(pysot)
            proposals.append(new_action)

        add_to_local_H(local_H, proposals)
        persistent.send(local_H[-len(proposals):][[i[0] for i in gen_specs['out']]])

        # Start work loop
        stop_generator = False

        while True:
            # Get results back from libE workers
            tag, Work, calc_in = persistent.recv()
            if tag in [STOP_TAG, PERSIS_STOP]:
                break
            # Send all results to pySOT that we got from libE workers
            for row in calc_in:
                for i in range(len(proposals)):
                    if proposals[i].record.sim_id == row['sim_id']:
                        break
                else:
                    raise ValueError("No matching sim_id found in proposal list")

                proposal = proposals.pop(i)
                if np.isnan(row['f']):
                    print('found nan')
                    proposal.record.cancel()
                else:
                    proposal.record.complete(row['f'])

            # Provide new evaluations for workers to work on
            new_proposals = 0
            for _ in range(calc_in.size):
                # Check if it is safe to request a new point
                if pysot.num_evals > surrogate_tail_dim or len(pysot.batch_queue) > 0:
                    # pysot may return a terminate proposal or None at this point
                    new_action = get_proposal(pysot)
                    if not new_action or new_action.action == 'terminate':
                        stop_generator = True

                    proposals.append(new_action)
                    new_proposals += 1

            if stop_generator:
                # If there is a batch of proposals that includes a terminate we don't process any proposals in batch
                break

            # Send new points to allocator - if any
            if new_proposals > 0:
                add_to_local_H(local_H, proposals[-calc_in.size:])
                persistent.send(local_H[-calc_in.size:][[i[0] for i in gen_specs['out']]])

        return local_H, persis_info, FINISHED_PERSISTENT_GEN_TAG
    finally:
        pass


def add_to_local_H(local_H, points):
    len_local_H = len(local_H)
    num_pts = len(points)

    local_H.resize(len(local_H)+num_pts, refcheck=False)  # Adds num_pts rows of zeros to O
    local_H['x'][-num_pts:] = [point.record.params[0] for point in points]
    sim_ids = np.arange(len_local_H, len_local_H+num_pts)
    local_H['sim_id'][-num_pts:] = sim_ids

    for sim_id, point in zip(sim_ids, points):
        point.record.sim_id = sim_id
