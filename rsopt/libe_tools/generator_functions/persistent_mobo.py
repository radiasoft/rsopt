import logging
import torch
import numpy as np
from botorch.utils.sampling import draw_sobol_samples
from xopt.bayesian.data import get_data_json
from xopt.bayesian import generators
from xopt.bayesian.utils import get_candidates

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG, EVAL_GEN_TAG
from libensemble.tools.persistent_support import PersistentSupport

# TODO: Coul implement a threshol that must be reache beore the model is evaluated
#       until then results are cashe (thouh requesting points is expensive)

"""
Need to pass in libE_info:
fixed_cost *
restart_file *
processes !
tkwargs *
ref !
generator_options * 
custom_model *
base_cost *
lb, ub !
constraints * 
budget !
"""

logger = logging.getLogger('libensemble')
logging.basicConfig(level=logging.DEBUG)


def configure_generator(vocs, ref, **generator_options):
    # If more generator options are added
    return generators.mobo.MOBOGenerator(vocs, ref, **generator_options)


def separate_data_in(points):
    return points


def add_to_local_H(local_H, points):
    x = separate_data_in(points)
    len_local_H = len(local_H)
    num_pts = len(points)

    local_H.resize(len(local_H)+num_pts, refcheck=False)  # Adds num_pts rows of zeros to O
    local_H['x'][-num_pts:] = x
    local_H['sim_id'][-num_pts:] = np.arange(len_local_H, len_local_H+num_pts)


def persistent_mobo(H, persis_info, gen_specs, libE_info):
    # Multi-Objective Bayesian Optimization
    # Implementation based on asynchronous update from:
    # https://github.com/ChristopherMayes/Xopt/blob/47ae31b2c2ae74584d612e42babd67883da753cd/xopt/bayesian/optim/asynch.py

    # libEnsemble Setup
    persistent = PersistentSupport(libE_info, EVAL_GEN_TAG)
    local_H = np.zeros(len(H), dtype=H.dtype)

    # MOBO Setup
    fixed_cost = True if gen_specs['user'].get('fixed_cost') else False  # TOdO: This is automatically set rom VOCS
    restart_file = gen_specs['user'].get('restart_file')
    initial_x = gen_specs['user'].get('initial_x')
    generator_options = gen_specs['user'].get('generator_options', {})
    custom_model = gen_specs['user'].get('custom_model')
    base_cost = gen_specs['user'].get('base_cost', 1.0)
    constraints = gen_specs['user'].get('constraints', {})
    budget = gen_specs['user']['budget']
    processes = gen_specs['user']['processes']
    ref = gen_specs['user']['ref']
    lb, ub = gen_specs['user']['lb'], gen_specs['user']['ub']

    # assemble necessary VOCS components
    vocs = {'variables': {str(i): [l, u] for i, (l, u) in enumerate(zip(lb, ub))},
            'objectives': {str(i): 'MINIMIZE' for i in range(gen_specs['out'][0][2][0])},
            'constraints': constraints}

    # create generator
    candidate_generator = configure_generator(vocs, ref, **generator_options)

    # track total cost of submitted candidates
    total_cost = 0

    # get data from previous runs, otherwise start with some initial samples
    if restart_file is None:
        # generate initial samples if no initial samples are given
        if initial_x is None:
            initial_x = draw_sobol_samples(
                torch.tensor(np.array([lb, ub]), **candidate_generator.tkwargs), 1, processes
            )[0]
        else:
            initial_x = initial_x

        # # add initial points to the queue
        # for ele in initial_x:
        #     q.put(ele)

        train_x, train_y, train_c, inputs, outputs = torch.empty(0, lb.size), \
                                                     torch.empty(0, lb.size), \
                                                     torch.empty(0, lb.size), None, None

    else:
        data = get_data_json(restart_file, vocs, **candidate_generator.tkwargs)
        train_x = data["variables"]
        train_y = data["objectives"]
        train_c = data["constraints"]

        # get a new set of candidates and put them in the queue
        logger.info(f"generating {processes} new candidate(s) from restart file")
        initial_x = get_candidates(
            train_x,
            train_y,
            vocs,
            candidate_generator,
            train_c=train_c,
            custom_model=custom_model,
            q=processes,
        )

    # Submit initial candidates and tally cost
    # TODO: setting submit count an hanling cost is not well implemente
    for submit_count, candidate in enumerate(initial_x):
        if fixed_cost:
            c = 1.0
        else:
            c = candidate[-1] + base_cost

        total_cost += c

        logger.info(
            f"Submitting candidate {submit_count:3}, cost: {c:4.3}, "
            f"total cost: {total_cost:4.4}"
        )
        logger.debug(f"{candidate}")

        if total_cost > budget:
            break

    add_to_local_H(local_H, initial_x[:submit_count+1])
    persistent.send(local_H[-len(initial_x[:submit_count+1]):][[g[0] for g in gen_specs['out']]])

    # do optimization
    logger.info("starting optimization loop")
    exceeded_budget = total_cost > budget

    while True:
        # Get results back from libE workers
        tag, Work, calc_in = persistent.recv()
        if tag in [STOP_TAG, PERSIS_STOP]:
            break

        # Process received evaluations
        if calc_in is not None:
            train_x, train_y, train_c = torch.vstack((train_x, torch.from_numpy(calc_in['x']))), \
                                        torch.vstack((train_y, torch.from_numpy(calc_in['f']))), \
                                        torch.vstack((train_c, torch.from_numpy(calc_in['c'])))
            # Update return status
            local_H['returned'][Work['libE_info']['H_rows']] = True
            # If budget remains, request new points
            if not exceeded_budget:
                logger.info(f"generating {len(calc_in)} new candidate(s)")

                # Check for pending evaluations
                if np.any(~local_H['returned']):
                    candidate_generator.X_pending = torch.from_numpy(local_H['x'][~local_H['returned']])

                new_candidates = get_candidates(
                    train_x,
                    train_y,
                    vocs,
                    candidate_generator,
                    train_c=train_c,
                    custom_model=custom_model,
                    q=len(calc_in),
                )

                # add new candidates to queue
                logger.debug("Adding candidates to queue")
            else:
                new_candidates = None

            if new_candidates is not None:
                for submit_count, candidate in enumerate(new_candidates):
                    if fixed_cost:
                        c = 1.0
                    else:
                        c = candidate[-1] + base_cost

                    total_cost += c

                    logger.info(
                        f"Submitting candidate {submit_count:3}, cost: {c:4.3}, "
                        f"total cost: {total_cost:4.4}"
                    )
                    logger.debug(f"{candidate}")

                    if total_cost > budget:
                        break
                add_to_local_H(local_H, new_candidates[:submit_count+1])
                persistent.send(local_H[-len(new_candidates[:submit_count+1]):][[g[0] for g in gen_specs['out']]])

    return local_H, persis_info, FINISHED_PERSISTENT_GEN_TAG
