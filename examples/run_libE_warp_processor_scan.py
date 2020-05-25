"""
mpiexec -n 3 python run_libE_warp_processor_scan.py --nworkers 2
"""
import os
import numpy as np

# Import libEnsemble items for this test
from libensemble.libE import libE
from rsopt.codes.warp.libe_sim import simulate_tec_runtime as sim_f
from rsopt.libe_tools.generator_functions.utility_generators import generate_mesh as gen_f
from rsopt.libe_tools.tools import create_empty_persis_info
from libensemble.tools import parse_args, save_libE_output
from time import time


# RUN SETTINGS

# Output/Run directory setup
# `base_directory` should be set before running this script
# Recommendations are provided below are well
base_directory = '/home/vagrant/jupyter/StaffScratch/cchall'
# For NERSC use
# base_directory = os.environ['SCRATCH']

RUN_NAME = 'SCAN1'
TEMPLATE_FILE = 'support/gpyopt_best.yaml'
RUN_DIR = os.path.join(base_directory, RUN_NAME)
TIME_LIMIT = 120.  # Time limit for each run in minutes
CHECKPOINTS = 1  # Steps per libE checkpoint

MESH = [[1, 2]]
EXACT_MESH = True  # True if user supplies the exact values for the scan
N = len(MESH)  # Parameter dimensionality
MAX = 2


# Set up and Run libEnsemble

# libEnsemble Setup                                                                                             
nworkers, is_master, libE_specs, _ = parse_args()
libE_specs['nworkers'] = nworkers

if is_master:
    if not os.path.isdir('./{}'.format(RUN_DIR)):
        os.mkdir('{}'.format(RUN_DIR))
    else:
        print("Stopping - Directory exists: {}".format(RUN_DIR))
        exit()


if CHECKPOINTS:
    libE_specs['save_every_k_sims'] = CHECKPOINTS
libE_specs['sim_dirs_make'] = False
libE_specs['ensemble_dir_path'] = RUN_DIR
libE_specs['sim_dir_copy_files'] = [TEMPLATE_FILE]

if is_master:
    start_time = time()


# Job Controller
from libensemble.executors.mpi_executor import MPIExecutor
jobctrl = MPIExecutor(auto_resources=True, central_mode=True)


# Sim App
sim_app = 'rsopt'
jobctrl.register_calc(full_path=sim_app, calc_type='sim')


# Setup for Run with APOSMM
USER_DICT = {
             'base_path': RUN_DIR,
             'time_limit': TIME_LIMIT * 60.,
             'template_file': os.path.split(TEMPLATE_FILE)[-1]
             }

sim_specs = {'sim_f': sim_f,
             'in': ['x'],
             'out': [('f', float)],
             'user': USER_DICT
             }

gen_out = [('x', float, (N,))]

gen_specs = {'gen_f': gen_f,
             'in': [],
             'out': gen_out,
             'user': {
                     'mesh_definition': MESH,
                     'exact_mesh': EXACT_MESH
                     }
             }

persis_info = create_empty_persis_info(libE_specs)  # {0: {'worker_num': 0}, 1: {'worker_num': 1}}
exit_criteria = {'sim_max': MAX}


# Perform the run
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info, libE_specs=libE_specs)

if is_master:
    print('[Manager]: Time taken =', time() - start_time, flush=True)
    save_libE_output(H, persis_info, __file__, nworkers)
