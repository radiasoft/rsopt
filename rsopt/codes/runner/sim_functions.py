from rsopt.codes.runner.Runner import Runner
from libensemble.message_numbers import WORKER_DONE, WORKER_KILL, TASK_FAILED
import os, logging
import numpy as np
from time import sleep


def sim_function_with_runner(H, persis_info, sim_specs, libE_info):
    logger = logging.getLogger('libensemble')
    logger.info('sim launching from {}'.format(os.getcwd()))
    
    # Worker 1 for libEnsemble (with APOSMM Generator) does not do sim evals 
    # but we are farming out to servers based on worker number
    # You should use nworkers = number_of_servers + 1 then workerID - 1 is [1, number_of_servers]
    # and we can assign to server
    
    try:
        persistant_worker_count = sim_specs['user']['persistant_worker_count']
    except KeyError:
        logger.warning("persistant_worker_count was not explicitly set. Assuming 1 persistant worker.")
        persistant_worker_count = 1
        
    server_id = libE_info['workerID'] - persistant_worker_count
    # Sleep time is used to make sure we do not start rsmpi jobs too closely together
    # past experience has shown this leads to fatal errors. Possibly due to temporary files that are created in the same location?
    st = server_id * 5.
    sleep(st)
    
    x = H['x'][0]
    base_schema = sim_specs['user']['base_schema']
    objective_function = sim_specs['user']['objective_function']
    
    # Run Simulations
    runner = Runner(base_schema.format(server_id), objective_function=objective_function)
    result = runner.run(x)
    print('result on {} is {}'.format(server_id, result))
    
    # Evaluate Result
    try:
        # Catch if runner encountered an error (most likely full loss from opal)
        error = result[1]
        print("Error detected.")
        print("Runner settings:\n{}".format(result[0]))
        outspecs = sim_specs['out']
        output = np.zeros(1, dtype=outspecs)
        output['f'][0] = 100e3
        return output, persis_info, TASK_FAILED
    except (TypeError, IndexError) as e:
        pass
                    
    outspecs = sim_specs['out']
    output = np.zeros(1, dtype=outspecs)
    output['f'][0] = result
    
    print("Worker {} finished. Result: {}".format(server_id, result))
    return output, persis_info, WORKER_DONE