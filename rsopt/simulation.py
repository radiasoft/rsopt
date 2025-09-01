import logging
import time
import numpy as np
import os
import rsopt.conversion
import rsopt.util
import typing
from libensemble import message_numbers
from libensemble.executors.executor import Executor
from rsopt.libe_tools import serial_python
from rsopt.configuration.schemas import code
from rsopt import environment

_POLL_TIME = 1  # seconds
_PENALTY = 1e9


def get_x_from_H(H: np.ndarray, sim_specs: dict) -> list:
    # 'x' may have different name depending on software being used
    # Assumes vector data

    x_name = sim_specs['in'][0]
    x = H[x_name][0]

    return x.tolist()


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
    def __init__(self, jobs: list[code.Code], objective_function: typing.Callable):
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

    def __call__(self, H: np.ndarray, persis_info: dict, sim_specs: dict, libE_info: dict):
        self.H = H
        self.persis_info = persis_info
        self.sim_specs = sim_specs
        self.libE_info = libE_info
        self.J['rand_stream'] = self.persis_info['rand_stream']
        x = get_x_from_H(H, self.sim_specs)

        halt_job_sequence = False
        parameter_index = 0

        for job in self.jobs:
            # Pair values in vector x with named settings/parameters
            args, kwargs = job.get_kwargs(x, parameter_index)
            parameter_index += len(job.parameters)
            self.J['inputs'] = kwargs

            # Call preprocess functions from user - if any
            if job.setup.preprocess:
                job.get_preprocess_function(self.J)

            # Values in kwargs may be changed by the user during pre-process so they must be passed back to the job
            job.generate_input_file(kwargs, '.', job.use_mpi)
            # Create env setup script if the user passed any environ variables to set
            env_setup_name = environment.generate_env_setup(job.setup.environment_variables)

            # Translate distributions
            if self.switchyard and job.setup.input_distribution:
                if os.path.exists(job.input_distribution):
                    os.remove(job.input_distribution)
                self.switchyard.write(job.input_distribution, job.code)

            if job.code == 'python' and not job.use_mpi:
                # Serial Python Job
                python_exec = serial_python.SERIAL_MODES[job.setup.serial_python_mode]
                if job.setup.argument_passing == code.ArgumentModes.KWARGS:
                    result_dict = python_exec(job.get_function, **kwargs)
                else:
                    result_dict = python_exec(job.get_function, args)
                f = result_dict[serial_python.RESULT]
                self.J['sim_status'] = result_dict[serial_python.CODE]
                # NOTE: Right now f is not passed to the objective function. Would need to go inside J. Or pass J into
                #       function job.execute(**kwargs)
            elif job.use_executor:
                # MPI Job or non-Python executable
                exctr = Executor.executor
                task = exctr.submit(env_script=env_setup_name if env_setup_name else None, **job._executor_arguments)
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
                    elif task.runtime > job.setup.timeout:
                        self.log.warning('Task Timed out, aborting Job chain')
                        self.J['sim_status'] = message_numbers.WORKER_KILL_ON_TIMEOUT
                        task.kill()  # Timeout
                        halt_job_sequence = True
                        break
            else:
                raise NotImplementedError(f"Execution mode for job type: {job.code} was not handled")

            if halt_job_sequence:
                break

            if job.setup.output_distribution:
                self.switchyard = rsopt.conversion.create_switchyard(job.output_distribution, job.code)
                self.J['switchyard'] = self.switchyard

            # Run postprocess
            if job.setup.postprocess:
                job.get_postprocess_function(self.J)

        if self.J['sim_status'] == message_numbers.WORKER_DONE and not halt_job_sequence:
            # Use objective function if given
            if self.objective_function:
                val = self.objective_function(self.J)
                output = format_evaluation(self.sim_specs, val)
                self.log.info('val: {}, output: {}'.format(val, output))
            else:
                # If only serial python was run then objective_function doesn't need to be defined
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
