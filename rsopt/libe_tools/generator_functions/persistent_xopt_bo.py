import pandas
import numpy as np
from xopt.generators import bayesian
from xopt.vocs import VOCS

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG, EVAL_GEN_TAG
from libensemble.tools.persistent_support import PersistentSupport

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('libensemble')
gen_log = logging.getLogger('gen-log')


def candidates_to_array(candidates: list[dict], vocs: VOCS) -> np.ndarray:
    """Take x from Xopt's list of dicts and put into an array."""
    dimension = len(vocs.variables.keys())
    num_entries = len(candidates)
    new_array = np.zeros([num_entries, dimension])

    for i, c in enumerate(candidates):
        new_array[i, :] = [c[v] for v in vocs.variables.keys()]

    return new_array


def array_to_candidates(array: np.ndarray, vocs: VOCS) -> list[dict]:
    """Take structured array containing x, f, and possibly c; and move to list of dicts for Xopt."""
    candidates = []
    for row in array:
        result = {**{k: v for k, v in zip(vocs.variables.keys(), row['x'])}}
        result = {**result, **{k: v for k, v in zip(vocs.objectives.keys(), row['f'])}}
        result = {**result, **{k: v for k, v in zip(vocs.constraints.keys(), row['c'])}}
        candidates.append(result)

    return candidates


def add_candidates_to_local_H(local_H: np.ndarray, candidates: np.ndarray) -> None:
    """Process data from sim_f workers and add to local history"""
    len_local_H = len(local_H)
    num_pts = len(candidates)

    local_H.resize(len(local_H) + num_pts, refcheck=False)  # Adds num_pts rows of zeros to O
    local_H['x'][-num_pts:] = candidates
    local_H['sim_id'][-num_pts:] = np.arange(len_local_H, len_local_H + num_pts)


def persistent_mobo(H, persis_info, gen_specs, libE_info):
    """
    libEnsemble persistent generator implementation of the asynchronous update Multi-Objective Bayseian Optimization
    routine from Xopt. See also: https://link.aps.org/doi/10.1103/PhysRevAccelBeams.24.062801

    """
    # libEnsemble Setup
    persistent = PersistentSupport(libE_info, EVAL_GEN_TAG)
    local_H = np.zeros(len(H), dtype=H.dtype)

    # MOBO Setup
    generator_options = gen_specs['user'].get('generator_options', {})
    constraints = gen_specs['user'].get('constraints', {})
    min_calc_to_remodel = gen_specs['user'].get('min_calc_to_remodel', 1)
    processes = gen_specs['user']['processes']
    ref = gen_specs['user']['ref']
    lb, ub = gen_specs['user']['lb'], gen_specs['user']['ub']
    use_cuda = generator_options.get('use_cuda', False)

    # assemble necessary VOCS components
    vocs = VOCS()
    vocs.variables = {'x'+str(i): [l, u] for i, (l, u) in enumerate(zip(lb, ub))}
    vocs.objectives = {'y'+str(i): 'MINIMIZE' for i in range(H.dtype['f'].shape[0])}
    vocs.constraints = constraints

    reference_dict = {'y'+str(i): v for i, v in enumerate(ref.values())}
    # create generator
    generator = bayesian.MOBOGenerator(vocs=vocs,
                                       reference_point=reference_dict,
                                       use_cuda=use_cuda,
                                       **generator_options)

    # TODO: Budget and total cost tracking originally allowed variable cost to be calculated or passed back to generator
    #       This isn't really needed for MOBO now but could be useful for multi-fidelity. Leaving in until that is checked.
    # track total cost of submitted candidates
    total_cost = 0
    budget = 1  #  Dummy variables for now, total_cost never increments

    # Get initial submissions from Xopt generator and send to libEnsemble allocator
    initial_num_samples = max(processes, min_calc_to_remodel)
    submissions = generator.vocs.random_inputs(initial_num_samples, seed=None, custom_bounds=None,
                                               include_constants=True
                  )
    submissions_array = candidates_to_array(submissions, vocs)
    add_candidates_to_local_H(local_H, submissions_array)
    persistent.send(local_H[-len(submissions):][[g[0] for g in gen_specs['out']]])

    # do optimization
    logger.info("Starting optimization loop")
    gen_cycle = 0
    calc_recv_since_remodel = 0

    while True:
        gen_log.debug("GENERATOR CYCLE STARTING {}".format(gen_cycle))

        # Get results back from libE workers
        tag, Work, calc_in = persistent.recv()
        if calc_in is not None:
            gen_log.debug("generator received back {} results".format(len(calc_in)))
        else:
            gen_log.debug("generator received back 0 results")
        gen_log.debug("generator received back calc_in: {}".format(calc_in))
        if tag in [STOP_TAG, PERSIS_STOP] or total_cost > budget:
            break

        # Process received evaluations
        if calc_in is not None:
            calc_recv_since_remodel += len(calc_in)

            # add returned data to Xopt generator
            generator.add_data(
                pandas.DataFrame(array_to_candidates(calc_in, vocs))
            )

            # Update return status
            local_H['given_back'][Work['libE_info']['H_rows']] = True

            # If budget remains and enough calcs received back: Train new model and get new candidates
            if not total_cost > budget and calc_recv_since_remodel >= min_calc_to_remodel:
                logger.info(f"generating {calc_recv_since_remodel} new candidate(s)")

                # TODO: MOBO default acquisition supports this but the interface to the af has been removed
                # # Check for pending evaluations
                # if np.any(~local_H['returned']):
                #     gen_log.debug(
                #         'Setting X_pending with {} entries'.format(local_H['x'][~local_H['returned']].shape[0]))
                #     gen_log.debug('Entry IDs {}'.format(np.where(~local_H['returned'])))
                #
                #     candidate_generator.X_pending = torch.from_numpy(local_H['x'][~local_H['returned']])

                new_candidates = generator.generate(n_candidates=calc_recv_since_remodel)

                calc_recv_since_remodel = 0
                logger.debug("Model re-trained and {} new candidates generated".format(len(new_candidates)))
            else:
                if total_cost > budget:
                    gen_log.debug('Eval budget exceeded. Budget: {}\nCost Total {}'.format(budget, total_cost))
                if calc_recv_since_remodel < min_calc_to_remodel:
                    gen_log.debug(
                        'Insufficient new calcs to remodel. Need: {}\nReceived: {}'.format(min_calc_to_remodel,
                                                                                           calc_recv_since_remodel))
                new_candidates = None

            if new_candidates is not None:
                logger.debug("Sending out {} new candidates for eval".format(len(submissions)))

                submissions_array = candidates_to_array(new_candidates, vocs)
                add_candidates_to_local_H(local_H, submissions_array)
                persistent.send(local_H[-len(submissions):][[g[0] for g in gen_specs['out']]])

        gen_cycle += 1
        gen_log.debug("\n\n")

    return None, persis_info, FINISHED_PERSISTENT_GEN_TAG
