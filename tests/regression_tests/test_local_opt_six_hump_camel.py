# python test_persistent_optimizer.py --nworkers 2 --comms local
import numpy as np
import libensemble.gen_funcs
libensemble.gen_funcs.rc.aposmm_optimizers = 'nlopt'
# Import libEnsemble items for this test
from libensemble.libE import libE
from libensemble.sim_funcs.six_hump_camel import six_hump_camel as sim_f
from rsopt.libe_tools.generator_functions.local_opt_generator import persistent_local_opt as gen_f
# from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens as alloc_f
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc as alloc_f
from libensemble.tools import parse_args, save_libE_output, add_unique_random_streams
from time import time

nworkers, is_master, libE_specs, _ = parse_args()

if is_master:
    start_time = time()

n = 2
sim_specs = {'sim_f': sim_f,
             'in': ['x'],
             'out': [('f', float)]}

gen_out = [('x', float, n), ('x_on_cube', float, n), ('sim_id', int),
           ('local_pt', bool)]

gen_specs = {'gen_f': gen_f,
             'in': [],
             'out': gen_out,
             'user': {'localopt_method': 'LN_BOBYQA',
                      'initial_sample_size': 1,  # this is need to use aposmm allocator, but is always 1 for local opts
                      'xstart': np.array([0.08, -0.7]), # near one global min
                      'xtol_abs': 1e-6,
                      'ftol_abs': 1e-6,
                      'lb': np.array([-3, -2]),
                      'ub': np.array([3, 2])}
             }

alloc_specs = {'alloc_f': alloc_f, 'out': [('given_back', bool)], 'user': {}}

persis_info = add_unique_random_streams({}, nworkers + 1)

exit_criteria = {'sim_max': 35}

# Perform the run
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info,
                            alloc_specs, libE_specs)


def test_optimizer_result():
    print("Best:", np.min(H['f']))
    six_hump_min_target = -1.031628445
    assert np.abs(six_hump_min_target - np.min(H['f'])) < 1e-12

test_optimizer_result()

