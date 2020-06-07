from rsopt.codes.runner.Runner import Runner
from libensemble.message_numbers import WORKER_DONE, WORKER_KILL, TASK_FAILED
import os
import numpy as np
from time import sleep


def sim_function_with_runner(H, persis_info, sim_specs, libE_info):
    print('sim launching from {}'.format(os.getcwd()))
    
    # Worker 1 for libEnsemble does not do sim evals but we are farming out to servers based on worker number
    # You should use nworkers = number_of_servers + 1 then workerID - 1 is [1, number_of_servers]
    # and we can assign to server
    server_id = libE_info['workerID'] - 1
    print('Server id is: {}'.format(server_id))
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