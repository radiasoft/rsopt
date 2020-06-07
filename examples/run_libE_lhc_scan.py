"""
Start with: python3 run_libE.py --nworkers 5 --comms local
Because JobRunner handles server assignment and executes rsmpi we will not have libEnsemble using an MPI communicator
it will run local (to head node) Python calls to execute JobRunner.run.

Though it we won't have sim_fuc == JobRunner.run since each execution requires a new instance or JobRunner
and libE needs different inputs/outputs than JobRunner provides. We'll have a simple wrapper around JobRunner that libE will directly call.


import obj_func

sim_func():
    worker_num = get_worker_number_from_libE()
    # schema for each server
    my_schema = schema_list[worker_num]
    my_runner = JobRunner(my_schema, obj_func)
    
    my_obj = my_runner.run()
    
    # give obj to libE
    
    return stuff_for_libE
    
"""

import os

from libensemble.libE import libE
from libensemble.gen_funcs.persistent_aposmm import aposmm as gen_f
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc as alloc_f
from libensemble.tools import parse_args, add_unique_random_streams

from rsopt.codes.runner.Runner import Runner
from rsopt.codes.runner.sim_functions import sim_function_with_runner as sim_f

# For the default sim_f a function must be supplied and will be called, but the output is not used in the scan
from rsopt.codes.runner.obj_functions import dummy as obj_f


# OPTIONS
SAMPLE_SIZE = 100
CHECKPOINTS = 5  # How frequently the H array data with be saved by libEnsemble
SCHEMA_DIR = './schema/'  # Place schema files in ./schema
BASE_SCHEMA = 'aposmm_schema_{}.yaml'  # Filename will be formatted with index when needed
# RUN_DIR is the base directory where libEnsemble workers will execute sim_f. libE will create new directories
#  in RUN_DIR for each worker execution.
RUN_DIR = '//INSERT YOUR PATH HERE'  # EXAMPLE: '/home/vagrant/jupyter/StaffScratch/my_github_username/scan1'

    
if not os.path.isdir('{}'.format(RUN_DIR)):
    os.mkdir('{}'.format(RUN_DIR))
else:
    print("Stopping - Directory exists: {}".format(RUN_DIR))
    exit()

# Set bounds for latin hypercube scan from schema min/max values
runner = Runner(os.path.join(SCHEMA_DIR, BASE_SCHEMA.format(1)), objective_function=None)
LB, UB, _ = runner.prepare_parameters()
N = LB.size


# libEnsemble Setup
nworkers, is_master, libE_specs, _ = parse_args()

if CHECKPOINTS:
    libE_specs['save_every_k_sims'] = CHECKPOINTS
libE_specs['use_worker_dirs'] = True
libE_specs['sim_input_dir'] = './schema' 
libE_specs['ensemble_dir'] = RUN_DIR
libE_specs['symlink_input_files'] = [BASE_SCHEMA.format(i) for i in range(1, nworkers)]


# Sim Setup
sim_specs = {'sim_f': sim_f,
             'in': ['x'],
             'out': [('f', float)],
             'user': {
                 'base_schema': BASE_SCHEMA,
                 'objective_function': obj_f
              }
             }

gen_specs = {'gen_f': gen_f,
             'out': [('x', float, N)],
             'user': {'gen_batch_size': SAMPLE_SIZE,
                      'lb': LB,
                      'ub': UB,
                      }
             }


# APOSMM Allocator Setup
alloc_specs = {'alloc_f': alloc_f, 'out': [('given_back', bool)], 'user': {}}
persis_info = add_unique_random_streams({}, nworkers + 1)


# Stopping Criteria
exit_criteria = {'gen_max': SAMPLE_SIZE+1}


# Perform the run
H, persis_info, flag = libE(sim_specs, gen_specs, exit_criteria, persis_info,
                            alloc_specs, libE_specs, H0=None)