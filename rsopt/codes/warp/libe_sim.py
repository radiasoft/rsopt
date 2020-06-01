import os, time, uuid
import numpy as np
from rsopt.codes.warp.tec_utilities import get_efficiency, create_settings_file
from libensemble.executors.executor import Executor
from libensemble.message_numbers import WORKER_DONE, WORKER_KILL, TASK_FAILED, WORKER_KILL_ON_TIMEOUT
import logging

def simulate_tec_efficiency(H, persis_info, sim_specs, libE_info):
    logger = logging.getLogger('libensemble')

    # Setup
    failure_penalty = sim_specs['user']['failure_penalty']
    base_path = sim_specs['user']['base_path']
    template_file = sim_specs['user']['template_file']
    sim_name, output_path = make_sim_name(base_path)
    create_input_schema(H, base_path, sim_name, template_file)
    logger.info('base_path: ' + base_path)
    logger.info('output_path: ' + output_path)
    logger.info('sim_name: ' + sim_name)

    calc_status = start_warp_task(H, sim_specs, sim_name+'.yaml',sim_name)
    if calc_status == WORKER_DONE:
        # There is an internal flag set in my Warp output if simulation hits a known failure mode
        # then failure_penalty is used. Otherwise read the calculated efficiency.
        try:
            efficiency = get_efficiency(output_path, sim_name, penalty=failure_penalty)
        except:
            print('Unknown error trying to read efficiency for Job {job} on Worker {worker}'.format(job=H['sim_id'],
                                                                                                    worker=H['sim_worker']))
            efficiency = failure_penalty
    else:
        # Use same failure_penalty if libE says simulation did not complete
        efficiency = failure_penalty

    output = create_output(sim_specs, efficiency)

    return output, persis_info, calc_status


def simulate_tec_runtime(H, persis_info, sim_specs, libE_info):
    # For use in run time scans with varying processor number

    x = H['x'][0][0]
    base_path = sim_specs['user']['base_path']
    template_file = sim_specs['user']['template_file']
    
    # Cores is normally set by user dict. Create temporary entry to mimic
    sim_specs_pass = sim_specs.copy()
    sim_specs_pass['user']['cores'] = x

    # Run simulation
    start_time = time.time()
    calc_status = start_warp_task(H, sim_specs_pass, template_file, str(int(x)))
    run_time = time.time() - start_time

    # Format output
    outspecs = sim_specs['out']
    output = np.zeros(1, dtype=outspecs)

    if calc_status == WORKER_DONE:
        output['f'][0] = run_time
    else:
        output['f'][0] = np.nan

    return output, persis_info, calc_status


def make_sim_name(base_path):

    sim_name = str(uuid.uuid4())
    dir_prefix = 'diags_id_'
    output_path = os.path.join(base_path, dir_prefix + sim_name)

    return sim_name, output_path


def start_warp_task(H, sim_specs, schema_file, sim_id):

    time_limit = sim_specs['user']['time_limit']
    cores = sim_specs['user']['cores']
    inputfile = 'run-tec-3d simulate-efficiency '
    inputfile += schema_file + ' '
    inputfile += '-r _'+sim_id
    exctr = Executor.executor
    stdout, stderr = 'out_'+sim_id+'.txt', 'err_'+sim_id+'.txt'

    if cores:
        # wait_on_run? was true for fmu work
        job = exctr.submit(calc_type='sim', num_procs=cores, app_args=inputfile, stdout=stdout, stderr=stderr)
    else:
        job = exctr.submit(calc_type='sim',  app_args=inputfile, stdout=stdout, stderr=stderr)
    poll_interval = 1.0  # secs

    while not job.finished:
        time.sleep(poll_interval)
        job.poll()
        if job.runtime > time_limit:
            job.kill()
            print('Job #... exceeded time limit')
            calc_status = WORKER_KILL_ON_TIMEOUT

        if job.finished:
            if job.state == 'FINISHED':
                calc_status = WORKER_DONE
            elif job.state == 'FAILED':
                calc_status = TASK_FAILED

    return calc_status


def create_input_schema(H, path, sim_id, base_file):

    x = H['x'][0]
    create_settings_file(path, sim_id, base_file, x)


def create_output(sim_specs, efficiency):
    outspecs = sim_specs['out']
    output = np.zeros(1, dtype=outspecs)
    scaled_efficiency = sim_specs['user']['scaling'](efficiency)
    output['f'][0] = scaled_efficiency

    return output
