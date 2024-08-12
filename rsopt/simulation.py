import logging
import time
import numpy as np
import os
import rsopt.conversion
import rsopt.util
from libensemble import message_numbers
from libensemble.executors.executor import Executor
from collections.abc import Iterable
from rsopt.codes.serial_python import RESULT, CODE
# TODO: This should probably be in libe_tools right?

_POLL_TIME = 1  # seconds
_PENALTY = 1e9


def get_x_from_H(H, sim_specs):
    # 'x' may have different name depending on software being used
    # Assumes vector data

    x_name = sim_specs['in'][0]
    x = H[x_name][0]

    return x.tolist()


def get_signature(parameters, settings):
    # TODO: signature just means dict with settings and params. This should be renamed if it is kept.
    # No lambda functions are allowed in settings and parameter names may not be referenced
    # Just needs to insert parameter keys into the settings dict, but they won't have usable values yet

    signature = settings.copy()

    for key in parameters.keys():
        signature[key] = None

    return signature


def _parse_x(x, parameters):
    x_struct = {}
    if not isinstance(x, Iterable):
        x = [x, ]
    for val, name in zip(x, parameters.keys()):
        x_struct[name] = val

    # Remove used parameters
    for _ in parameters.keys():
        x.pop(0)

    return x_struct


def compose_args(x, parameters, settings):
    args = None  # Not used for now
    x_struct = _parse_x(x, parameters)
    signature = get_signature(parameters, settings)
    kwargs = signature.copy()
    for key in kwargs.keys():
        if key in x_struct:
            kwargs[key] = x_struct[key]

    return args, kwargs


def format_evaluation(sim_specs, container):
    if not hasattr(container, '__iter__'):
        container = (container,)
    # FUTURE: Type check for container values against spec
    outspecs = sim_specs['out']
    output = np.zeros(1, dtype=outspecs)

    if len(outspecs) == 1:
        output[output.dtype.names[0]] = container
        return output

    for spec, value in zip(output.dtype.names, container):
        output[spec] = value

    return output


class SimulationFunction:
    def __init__(self, jobs: list, objective_function: list):
        # Received from libEnsemble during function evaluation
        self.H = None
        self.J = {}
        self.persis_info = None
        self.sim_specs = None
        self.libE_info = None
        self.log = logging.getLogger('libensemble')
        self.jobs = jobs
        self.objective_function = objective_function
        self.switchyard = None

    def __call__(self, H, persis_info, sim_specs, libE_info):
        self.H = H
        self.persis_info = persis_info
        self.sim_specs = sim_specs
        self.libE_info = libE_info
        self.J['rand_stream'] = self.persis_info['rand_stream']
        x = get_x_from_H(H, self.sim_specs)

        halt_job_sequence = False

        for job in self.jobs:
            # Generate input values
            _, kwargs = compose_args(x, job.parameters, job.settings)
            self.J['inputs'] = kwargs
            # Call preprocessors
            for f_pre in job.pre_process:
                f_pre(self.J)
            # Generate input files for simulation
            job._setup.generate_input_file(kwargs, '.', job.use_mpi)
            if self.switchyard and job.input_distribution:
                if os.path.exists(job.input_distribution):
                    os.remove(job.input_distribution)
                self.switchyard.write(job.input_distribution, job.code)
            
            job_timeout_sec = job.timeout
            
            if job.executor:
                # MPI Job or non-Python executable
                exctr = Executor.executor
                task = exctr.submit(**job.executor_args)
                while True:
                    time.sleep(_POLL_TIME)
                    task.poll()
                    if task.finished:
                        if task.state == 'FINISHED':
                            self.J['sim_status'] = message_numbers.WORKER_DONE
                            f = None
                            break
                        elif task.state == 'FAILED':
                            self.J['sim_status'] = message_numbers.TASK_FAILED
                            halt_job_sequence = True
                            break
                        else:
                            self.log.warning("Unknown task failure")
                            self.J['sim_status'] = message_numbers.TASK_FAILED
                            halt_job_sequence = True
                            break
                    elif task.runtime > job_timeout_sec:
                        self.log.warning('Task Timed out, aborting Job chain')
                        self.J['sim_status'] = message_numbers.WORKER_KILL_ON_TIMEOUT
                        task.kill()  # Timeout
                        halt_job_sequence = True
                        break
            else:
                # Serial Python Job
                result_dict = job.execute(**kwargs)
                f = result_dict[RESULT]
                self.J['sim_status'] = result_dict[CODE]
                # NOTE: Right now f is not passed to the objective function. Would need to go inside J. Or pass J into
                #       function job.execute(**kwargs)

            if halt_job_sequence:
                break

            if job.output_distribution:
                self.switchyard = rsopt.conversion.create_switchyard(job.output_distribution, job.code)
                self.J['switchyard'] = self.switchyard

            for f_post in job.post_process:
                f_post(self.J)

        if self.J['sim_status'] == message_numbers.WORKER_DONE and not halt_job_sequence:
            # Use objective function if given
            _obj_f = rsopt.util.get_objective_function(self.objective_function)
            if _obj_f:
                val = _obj_f(self.J)
                output = format_evaluation(self.sim_specs, val)
                self.log.info('val: {}, output: {}'.format(val, output))
            else:
                # If only serial python was run then then objective_function doesn't need to be defined
                try:
                    output = format_evaluation(self.sim_specs, f)
                except NameError as e:
                    print(e)
                    print("An objective function must be defined if final Job is is not Python")
        else:
            # TODO: Temporary penalty. Need to add a way to adjust this.
            self.log.warning('Penalty was used because result could not be evaluated')
            output = format_evaluation(self.sim_specs, _PENALTY)

        return output, persis_info, self.J['sim_status']