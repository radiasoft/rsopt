
import os
import numpy as np

# Import libEnsemble items for this test
from libensemble.libE import libE
from libe_sim import sim_func as sim_f
from libe_tools.generator_functions.utility_generators import generate_mesh as gen_f
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc as alloc_f
from libensemble.tools import parse_args, save_libE_output, add_
from time import time


# RUN SETTINGS
RUN_NAME = 'SCAN1'
TEMPLATE_FILE = 'gpyopt_best.yaml'
RUN_DIR = os.path.join(os.environ['SCRATCH'], RUN_NAME)
CHECKPOINT_FILE = None
CHECKPOINTS = 1  # Steps per libE checkpoint
INIT_SAMPLES = 6  # APOSMM initial sample count
N = 3  # Parameter dimensionality

# libEnsemble Setup                                                                                             
nworkers, is_master, libE_specs, _ = parse_args()

if is_master:
    if not os.path.isdir('./{}'.format(RUN_DIR)):
        os.mkdir('{}'.format(RUN_DIR))
    else:
        print("Stopping - Directory exists: {}".format(RUN_DIR))
        exit()


if CHECKPOINTS:
    libE_specs['save_every_k_sims'] = CHECKPOINTS
# libE_specs['use_worker_dirs'] = True  # Probably don't want here because we need to read from disk to get efficiency
libE_specs['ensemble_dir'] = RUN_DIR
# libE_specs['symlink_input_files'] = [BASE_SCHEMA.format(i) for i in range(1, nworkers)]

if is_master:
    start_time = time()


# Job Controller
from libensemble.executors.mpi_executor import MPIExecutor
jobctrl = MPIExecutor(auto_resources=True, central_mode=True)


# Sim App
sim_app = 'python'
jobctrl.register_calc(full_path=sim_app, calc_type='sim')


# Setup for Run with APOSMM
USER_DICT = {
             'failure_penalty': -10.,
             'base_path': RUN_DIR,
             'cores': 34,
             'time_limit': 30. * 60.,
             'template_file': TEMPLATE_FILE
             }

sim_specs = {'sim_f': sim_f,
             'in': ['x'],
             'out': [('f', float)],
             'user': USER_DICT
             }

gen_out = [('x', float, N), ('x_on_cube', float, N), ('sim_id', int),
           ('local_min', bool), ('local_pt', bool)]

gen_specs = {'gen_f': gen_f,
             'in': [],
             'out': gen_out,
             'user': {'initial_sample_size': INIT_SAMPLES,
                      'localopt_method': 'LN_BOBYQA',
                      # 'num_pts_first_pass': nworkers - 1,
                      'xtol_rel': 1e-12,
                      'ftol_rel': 1e-12,
                      'high_priority_to_best_localopt_runs': True,
                      'num_active_gens': 3,  # Can't find where this passed to may be from old version
                      'max_active_runs': 6,
                      'lb': np.array([.0, 0.12, 0.5]),
                      'ub': np.array([1.0, 0.88, 2.5])}
             }

alloc_specs = {'alloc_f': alloc_f, 'out': [('given_back', bool)], 'user': {'batch_mode': True}}
persis_info = add_unique_random_streams({}, nworkers + 1)
exit_criteria = {'sim_max': 16}

# Perform the run
# Load from Checkpoint if requested
if CHECKPOINT_FILE:
    H0 = np.load(CHECKPOINT_FILE)
    H0 = H0[H0['given_back'] * H0['returned']]  # Remove points that failed to evaluate before end of run
else:
    H0 = None


# Perform the run
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info,
                            alloc_specs, libE_specs, H0=H0)

if is_master:
    print('[Manager]: Time taken =', time() - start_time, flush=True)
    save_libE_output(H, persis_info, __file__, nworkers)
