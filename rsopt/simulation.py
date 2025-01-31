import logging
import time
import numpy as np
import os
import rsopt.conversion
import rsopt.util
import typing
from libensemble import message_numbers
from libensemble.executors.executor import Executor
from collections.abc import Iterable
from rsopt.codes import serial_python
from rsopt.configuration.schemas import code
from rsopt import environment
# TODO: This should probably be in libe_tools right?

_POLL_TIME = 1  # seconds
_PENALTY = 1e9


def get_x_from_H(H: np.ndarray, sim_specs: dict) -> list:
    # 'x' may have different name depending on software being used
    # Assumes vector data

    x_name = sim_specs['in'][0]
    x = H[x_name][0]

    return x.tolist()

# TODO: May be removed
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
    for val, name in zip(x, [param.name for param in parameters]):
        x_struct[name] = val

    # TODO: From inspection I don't see how this is needed
    # # Remove used parameters
    # for _ in parameters.keys():
    #     x.pop(0)

    return x_struct


def compose_args(x: list, parameters: list, settings: list):
    # Generate the list of args and dict of kwargs from the configuration's parameters and settings
    # Matches the values from the 'x' list to the corresponding names from the parameters
    args = None  # Not used for now
    parameters_dict = _parse_x(x, parameters)
    settings_dict = {s.name: s.value for s in settings}
    kwargs = {**parameters_dict, **settings_dict}

    # TODO: Remove if new method above works
    # signature = get_signature(parameters, settings)
    # kwargs = signature.copy()
    # for key in kwargs.keys():
    #     if key in x_struct:
    #         kwargs[key] = x_struct[key]

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

        for job in self.jobs:
            # Generate input values
            _, kwargs = compose_args(x, job.parameters, job.settings)
            self.J['inputs'] = kwargs

            # Call preprocessor
            if job.setup.preprocess:
                job.get_preprocess_function(self.J)

            # Generate input files for simulation
            job.generate_input_file(kwargs, '.', job.use_mpi)
            # Create env setup script if required
            env_setup_name = environment.generate_env_setup(job.setup.environment_variables)

            # Translate distributions
            if self.switchyard and job.setup.input_distribution:
                if os.path.exists(job.input_distribution):
                    os.remove(job.input_distribution)
                self.switchyard.write(job.input_distribution, job.code)

            if job.code == 'python':
                # Serial Python Job
                python_exec = serial_python.SERIAL_MODES[job.setup.serial_python_mode]
                result_dict = python_exec(job.get_function, **kwargs)
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