import logging
import time
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
            job.setup.generate_input_file(kwargs)

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
                job.execute(**kwargs)
                sim_status = 'FINISHED'

        if sim_status == 'FINISHED' and self.objective_function:
            self.objective_function()