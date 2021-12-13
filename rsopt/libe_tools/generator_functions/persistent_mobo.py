import torch
import numpy as np
from botorch.utils.sampling import draw_sobol_samples
from xopt.bayesian.data import get_data_json
from xopt.bayesian import generators
from xopt.bayesian.utils import get_candidates

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG, EVAL_GEN_TAG
from libensemble.tools.persistent_support import PersistentSupport

import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('libensemble')
gen_log = logging.getLogger('gen-log')


def configure_generator(vocs: dict, ref: list, **generator_options) -> generators.mobo.MOBOGenerator:
    """Setup generator"""
    # If more generator options are adde
    return generators.mobo.MOBOGenerator(vocs, ref, **generator_options)


def process_x(points: torch.Tensor, use_cuda: bool = False) -> torch.Tensor:
    if use_cuda:
        return points.cpu()
    return points


def add_to_local_H(local_H: np.ndarray, points: torch.Tensor, use_cuda: bool = False) -> None:
    """Process data from sim_f workers and add to local history"""
    x = process_x(points, use_cuda)
    len_local_H = len(local_H)
    num_pts = len(points)

    local_H.resize(len(local_H) + num_pts, refcheck=False)  # Adds num_pts rows of zeros to O
    local_H['x'][-num_pts:] = x
    local_H['sim_id'][-num_pts:] = np.arange(len_local_H, len_local_H + num_pts)


def generate_new_candidates(x: torch.Tensor, y: torch.Tensor, c: torch.Tensor,
                            vocs: dict, candidate_generator: generators.mobo.MOBOGenerator,
                            candidates: int, custom_model=None, cuda: bool = False) -> torch.Tensor:
    """Return new candidates that will be sent to workers"""
    if cuda:
        # Model is on GPU - move data from generator over
        x = x.to(torch.device('cuda'))
        y = y.to(torch.device('cuda'))
        c = c.to(torch.device('cuda'))

    new_candidates = get_candidates(
        x, y,
        vocs,
        candidate_generator,
        train_c=c,
        custom_model=custom_model,
        q=candidates)

    return new_candidates


def budgeting(x: torch.Tensor, base_cost: float, total_cost: float,
              budget: float, fixed_cost: bool = True) -> (float, torch.Tensor):
    """Tracks evaluation budget and truncates submission list if budget exceeded"""
    submit = 0

    for candidate in x:
        if fixed_cost:
            c = 1.0
        else:
            c = candidate[-1] + base_cost

        total_cost += c

        logger.info(
            f"Accepting submission candidate {candidate}, cost: {c:4.3}, "
            f"Total cost: {total_cost:4.4}"
        )

        submit += 1

        if total_cost > budget:
            break

    return total_cost, x[:submit]


def persistent_mobo(H, persis_info, gen_specs, libE_info):
    # libEnsemble Setup
    persistent = PersistentSupport(libE_info, EVAL_GEN_TAG)
    local_H = np.zeros(len(H), dtype=H.dtype)

    # MOBO Setup
    fixed_cost = True if gen_specs['user'].get('fixed_cost') else False
    restart_file = gen_specs['user'].get('restart_file')
    initial_x = gen_specs['user'].get('initial_x')
    generator_options = gen_specs['user'].get('generator_options', {})
    custom_model = gen_specs['user'].get('custom_model')
    base_cost = gen_specs['user'].get('base_cost', 1.0)
    constraints = gen_specs['user'].get('constraints', {})
    min_calc_to_remodel = gen_specs['user'].get('min_calc_to_remodel', 1)
    budget = gen_specs['user']['budget']
    processes = gen_specs['user']['processes']
    ref = gen_specs['user']['ref']
    lb, ub = gen_specs['user']['lb'], gen_specs['user']['ub']
    use_cuda = generator_options.get('use_gpu', False)

    # assemble necessary VOCS components
    vocs = {'variables': {str(i): [l, u] for i, (l, u) in enumerate(zip(lb, ub))},
            'objectives': {str(i): 'MINIMIZE' for i in range(H.dtype['f'].shape[0])},
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

        train_x, train_y, train_c, inputs, outputs = torch.empty(0, len(vocs['variables'])), \
                                                     torch.empty(0, len(vocs['objectives'])), \
                                                     torch.empty(0, len(vocs['constraints'])), None, None

    else:
        data = get_data_json(restart_file, vocs, **candidate_generator.tkwargs)
        train_x = data["variables"]
        train_y = data["objectives"]
        train_c = data["constraints"]

        # get a new set of candidates and put them in the queue
        logger.info(f"generating {processes} new candidate(s) from restart file")
        initial_x = generate_new_candidates(train_x, train_y, train_c, vocs, candidate_generator, processes,
                                            custom_model=custom_model, cuda=use_cuda)

    # Submit initial candidates and tally cost
    total_cost, submissions = budgeting(initial_x, base_cost, total_cost, budget, fixed_cost)
    add_to_local_H(local_H, submissions, use_cuda)
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
            train_x, train_y, train_c = torch.vstack((train_x, torch.from_numpy(calc_in['x']))), \
                                        torch.vstack((train_y, torch.from_numpy(calc_in['f']))), \
                                        torch.vstack((train_c, torch.from_numpy(calc_in['c'])))
            # Update return status
            local_H['returned'][Work['libE_info']['H_rows']] = True

            # If budget remains and enough calcs received back: Train new model and get new candidates
            if not total_cost > budget and calc_recv_since_remodel >= min_calc_to_remodel:
                logger.info(f"generating {len(calc_in)} new candidate(s)")

                # Check for pending evaluations
                if np.any(~local_H['returned']):
                    gen_log.debug(
                        'Setting X_pending with {} entries'.format(local_H['x'][~local_H['returned']].shape[0]))
                    gen_log.debug('Entry IDs {}'.format(np.where(~local_H['returned'])))
                    candidate_generator.X_pending = torch.from_numpy(local_H['x'][~local_H['returned']])

                new_candidates = generate_new_candidates(train_x, train_y, train_c,
                                                         vocs, candidate_generator, calc_recv_since_remodel,
                                                         cuda=use_cuda)

                calc_recv_since_remodel = 0
                logger.debug("Model re-trained and {} new candidates generated".format(new_candidates.size))
            else:
                if total_cost > budget:
                    gen_log.debug('Eval budget exceeded. Budget: {}\nCost Total {}'.format(budget, total_cost))
                if calc_recv_since_remodel < min_calc_to_remodel:
                    gen_log.debug(
                        'Insufficient new calcs to remodel. Need: {}\nReceived: {}'.format(min_calc_to_remodel,
                                                                                           calc_recv_since_remodel))
                new_candidates = None

            if new_candidates is not None:
                total_cost, submissions = budgeting(new_candidates, base_cost,
                                                    total_cost, budget, fixed_cost)

                add_to_local_H(local_H, submissions, use_cuda)
                persistent.send(local_H[-len(submissions):][[g[0] for g in gen_specs['out']]])

        gen_cycle += 1
        gen_log.debug("\n\n")

    return None, persis_info, FINISHED_PERSISTENT_GEN_TAG
