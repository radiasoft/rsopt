# TODO: Need to figure out how to verify test works.
#  pySOT does not return a consistent result and won't find the 'exact' minimum

import numpy as np
import time
from libensemble.libE import libE
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens as alloc_f
from libensemble.tools import parse_args, add_unique_random_streams
from rsopt.libe_tools.generator_functions.persistent_pysot import persistent_pysot as gen_f
nworkers, is_manager, libE_specs, _ = parse_args()


def ackley(H, persis_info, sim_specs, other):
    xvals = H['x'][0]
    dim = xvals.size

    # Directly from pySOT Ackley implementation
    f = -20.0 * np.exp(-0.2 * np.sqrt(np.sum(xvals ** 2) / dim)) \
        - np.exp(np.sum(np.cos(2.0 * np.pi * xvals)) / dim) \
        + 20 \
        + np.exp(1)

    Out = np.zeros(1, dtype=sim_specs['out'])
    Out['f'] = f

    return Out, persis_info


if is_manager:
    start_time = time.time()

assert nworkers >= 2, "Cannot run with a persistent gen_f if only one worker."

dim = 10
lb = -15 * np.ones(dim)
ub = 20 * np.ones(dim)
max_evals = 500

# State the objective function, its arguments, output, and necessary parameters (and their sizes)
sim_specs = {'sim_f': ackley,  # This is the function whose output is being minimized
             'in': ['x'],  # These keys will be given to the above function
             'out': [('f', float)]  # This output is being minimized
             }  # end of sim spec

# State the generating function, its arguments, output, and necessary parameters.
gen_specs = {'gen_f': gen_f,
             'in': [],
             'out': [('x', float, dim), ],
             'user': {'lb': lb,
                      'ub': ub,
                      'dim': dim,
                      'max_evals': max_evals,
                      'threads': nworkers - 1}  # 1 worker used by generator
             }  # end gen specs

# libE Allocation function
alloc_specs = {'out': [('given_back', bool)], 'alloc_f': alloc_f,
               'user': {'async_return': True, 'active_recv_gen': True}}

# Tell libEnsemble when to stop
exit_criteria = {'sim_max': max_evals}


persis_info = add_unique_random_streams({}, nworkers + 1)

if is_manager:
    H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info, alloc_specs, libE_specs)
    print("Best result", np.min(H['f']))
    print("Best result is at", H['x'][np.argmin(H['f'])])
    print("Was found at iteration", np.argmin(H['f']))
