import logging
import time
import numpy as np
from libensemble.message_numbers import WORKER_DONE, WORKER_KILL, TASK_FAILED
from libensemble.executors.executor import Executor

# TODO: This should probably be in libe_tools right?

_POLL_TIME = 1  # seconds


def get_x_from_H(H):
    # Assumes vector data
    x = H['x'][0]
    return x

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
    for val, name in zip(x, parameters.keys()):
        x_struct[name] = val

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
    for spec, value in zip(output.dtype.names, container):
        output[spec] = value

    return output

class SimulationFunction:

    def __init__(self, jobs: list, objective_function: callable):
        # Received from libEnsemble during function evaluation
        self.H = None
        self.persis_info = None
        self.sim_specs = None
        self.libE_info = None
        self.log = logging.getLogger('libensemble')
        self.jobs = jobs
        self.objective_function = objective_function


    def __call__(self, H, persis_info, sim_specs, libE_info):
        self.H = H
        self.persis_info = persis_info
        self.sim_specs = sim_specs
        self.libE_info = libE_info

        x = get_x_from_H(H)

        for job in self.jobs:
            _, kwargs = compose_args(x, job.parameters, job.settings)
            job._setup.generate_input_file(kwargs, '.')  # TODO: Worker needs to be in their own directory

            if job.executor:
                # MPI Job or non-Python executable
                exctr = Executor.executor
                task = exctr.submit(**job.executor_args)
                while not task.finished:
                    time.sleep(_POLL_TIME)
                    if task.finished:
                        if job.state == 'FINISHED':
                            sim_status = 'FINISHED'
                            pass
                        elif job.state == 'FAILED':
                            sim_status = 'FAILED'
            else:
                # Serial Python Job
                f = job.execute(**kwargs)
                print("f is!!", f)
                sim_status = 'FINISHED'

        if sim_status == 'FINISHED' and self.objective_function:
            output = format_evaluation(self.sim_specs, self.objective_function())
        else:
            try:
                output = format_evaluation(self.sim_specs, f)
            except NameError as e:
                print(e)
                print("An objective function must be defined if final Job is is not Python")


        return output, persis_info, WORKER_DONE