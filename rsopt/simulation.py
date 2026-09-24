import logging
import time
import numpy as np
import os
import rsopt.conversion
import typing
from libensemble import message_numbers
from libensemble.executors.executor import Executor
from libensemble.resources.resources import Resources
from rsopt.libe_tools import serial_python
from rsopt.configuration.schemas import code
from rsopt import environment

_POLL_TIME = 1  # seconds
_PENALTY = 1e9


def get_x_from_H(H: np.ndarray, sim_specs: dict) -> list:
    # 'x' may have different name depending on software being used
    # Assumes vector data

    x_name = sim_specs["in"][0]
    x = H[x_name][0]

    return x.tolist()


def format_evaluation(sim_specs, container):
    if not hasattr(container, "__iter__"):
        container = (container,)
    # FUTURE: Type check for container values against spec
    outspecs = sim_specs["out"]
    output = np.zeros(1, dtype=outspecs)

    if len(outspecs) == 1:
        output[output.dtype.names[0]] = container
        return output

    for spec, value in zip(output.dtype.names, container):
        output[spec] = value

    return output


def _get_worker_resources():
    return Resources.resources.worker_resources if Resources.resources else None


def translate_gpu_slots(worker_resources, devices: list[int]) -> list[int]:
    """Map the GPUs libEnsemble assigned to this worker onto the device indices allowed by `gpu_options.devices`.

    libEnsemble numbers GPUs on a node from 0 by slot. When `gpu_options.devices` is set libEnsemble is told there are
    `len(devices)` GPUs per node, so each GPU number it assigns is an index into `devices`.

    Args:
        worker_resources: libEnsemble WorkerResources for this worker.
        devices: (list) Device indices each node may use.

    Returns:
        (list) Device indices on each node for this worker.
    """
    assert worker_resources.matching_slots, (
        f"GPU slots differ across nodes: {worker_resources.slots}"
    )
    per_slot = worker_resources.gpus_per_rset_per_node
    indices = [
        i
        for s in worker_resources.slots_on_node
        for i in range(s * per_slot, (s + 1) * per_slot)
    ]
    if not indices or max(indices) >= len(devices):
        raise ValueError(
            f"GPU slot indices {indices} out of range for gpu_options.devices {devices}"
        )

    return [devices[i] for i in indices]


def _gpu_env_name(worker_resources) -> str:
    # Same choice of variable as libEnsemble's WorkerResources.set_env_to_gpus
    platform_info = worker_resources.platform_info
    if platform_info is not None:
        if platform_info.get("gpu_setting_type") == "env":
            return platform_info.get("gpu_setting_name")
        return platform_info.get("gpu_env_fallback") or "CUDA_VISIBLE_DEVICES"
    return "CUDA_VISIBLE_DEVICES"


def set_worker_gpu_env(devices: list[int] = None) -> dict:
    """Restrict GPU visibility to the GPUs libEnsemble assigned to this worker.

    libEnsemble only assigns GPUs itself for MPIExecutor tasks. For jobs run in-process or as serial subprocesses the
    worker's GPU slots are applied by setting the platform's GPU environment variable (e.g. CUDA_VISIBLE_DEVICES).
    If `devices` is given the slots are mapped onto those device indices (see `translate_gpu_slots`), which is also
    used for MPI jobs in place of libEnsemble's own assignment.

    Args:
        devices: (list) Device indices from `gpu_options.devices`, or None to use libEnsemble's slot numbering.

    Returns:
        (dict) Prior values of any environment variables that were changed (None if previously unset), to be passed to
        `restore_env`.
    """
    worker_resources = _get_worker_resources()
    if worker_resources is None or not worker_resources.doihave_gpus():
        logging.getLogger("libensemble").warning(
            "gpu was requested but no GPUs are assigned to this worker"
        )
        return {}

    before = dict(os.environ)
    if devices:
        os.environ[_gpu_env_name(worker_resources)] = ",".join(
            str(d) for d in translate_gpu_slots(worker_resources, devices)
        )
    else:
        worker_resources.set_env_to_gpus()

    return {k: before.get(k) for k, v in os.environ.items() if before.get(k) != v}


def gpu_device_executor_arguments(executor_arguments: dict, devices: list[int]) -> dict:
    """Executor.submit() arguments for an MPI GPU job when `gpu_options.devices` is set.

    libEnsemble's auto_assign_gpus would set the GPU variable to its own slot numbering in the task environment, so it
    is disabled and the variable is set by `set_worker_gpu_env` instead. match_procs_to_gpus has no effect without
    auto_assign_gpus, so the equivalent layout is set explicitly: one MPI rank per visible GPU on each of the worker's
    nodes.

    Args:
        executor_arguments: (dict) Arguments from `create_executor_arguments`.
        devices: (list) Device indices from `gpu_options.devices`.

    Returns:
        (dict) Updated copy of `executor_arguments`.
    """
    worker_resources = _get_worker_resources()
    if worker_resources is None or not worker_resources.doihave_gpus():
        # Leave assignment to libEnsemble, which will report the missing GPUs
        return executor_arguments

    gpus_per_node = len(translate_gpu_slots(worker_resources, devices))

    return {
        **executor_arguments,
        "auto_assign_gpus": False,
        "match_procs_to_gpus": False,
        "num_nodes": worker_resources.local_node_count,
        "procs_per_node": gpus_per_node,
    }


def restore_env(previous: dict) -> None:
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


class SimulationFunction:
    def __init__(
        self,
        jobs: list[code.Code],
        objective_function: typing.Callable,
        gpu_devices: list[int] = None,
    ):
        # Received from libEnsemble during function evaluation
        self.H = None
        self.J = {}
        self.persis_info = None
        self.sim_specs = None
        self.libE_info = None
        self.log = logging.getLogger("libensemble")
        self.jobs = jobs
        self.objective_function = objective_function
        self.gpu_devices = gpu_devices
        self.switchyard = None

    def __call__(
        self, H: np.ndarray, persis_info: dict, sim_specs: dict, libE_info: dict
    ):
        self.H = H
        self.persis_info = persis_info
        self.sim_specs = sim_specs
        self.libE_info = libE_info
        self.J["rand_stream"] = self.persis_info["rand_stream"]
        x = get_x_from_H(H, self.sim_specs)

        halt_job_sequence = False
        parameter_index = 0

        for job in self.jobs:
            # Pair values in vector x with named settings/parameters
            args, kwargs = job.get_kwargs(x, parameter_index)
            parameter_index += len(job.parameters)
            self.J["inputs"] = kwargs

            # Call preprocess functions from user - if any
            if job.setup.preprocess:
                job.get_preprocess_function(self.J)

            # Values in kwargs may be changed by the user during pre-process so they must be passed back to the job
            job.generate_input_file(kwargs, ".", job.use_mpi)
            # Create env setup script if the user passed any environ variables to set
            env_setup_name = environment.generate_env_setup(
                job.setup.environment_variables
            )

            # Translate distributions
            if self.switchyard and job.setup.input_distribution:
                if os.path.exists(job.input_distribution):
                    os.remove(job.input_distribution)
                self.switchyard.write(job.input_distribution, job.code)

            # MPI jobs get GPUs through MPIExecutor's auto_assign_gpus unless gpu_options.devices is set
            if job.setup.gpu and (not job.use_mpi or self.gpu_devices):
                gpu_env = set_worker_gpu_env(self.gpu_devices)
            else:
                gpu_env = {}
            if gpu_env:
                self.log.debug(
                    f"Worker GPU environment set: { {k: os.environ[k] for k in gpu_env} }"
                )

            if job.code == "python" and not job.use_mpi:
                # Serial Python Job
                python_exec = serial_python.SERIAL_MODES[job.setup.serial_python_mode]
                if job.setup.argument_passing == code.ArgumentModes.KWARGS:
                    result_dict = python_exec(job.get_function, **kwargs)
                else:
                    result_dict = python_exec(job.get_function, args)
                f = result_dict[serial_python.RESULT]
                self.J["sim_status"] = result_dict[serial_python.CODE]
                # NOTE: Right now f is not passed to the objective function. Would need to go inside J. Or pass J into
                #       function job.execute(**kwargs)
            elif job.use_executor:
                # MPI Job or non-Python executable
                exctr = Executor.executor
                executor_arguments = job._executor_arguments
                if job.setup.gpu and job.use_mpi and self.gpu_devices:
                    executor_arguments = gpu_device_executor_arguments(
                        executor_arguments, self.gpu_devices
                    )
                task = exctr.submit(
                    env_script=env_setup_name if env_setup_name else None,
                    **executor_arguments,
                )
                while True:
                    time.sleep(_POLL_TIME)
                    task.poll()
                    if task.finished:
                        if task.state == "FINISHED":
                            self.J["sim_status"] = message_numbers.WORKER_DONE
                            f = None
                            break
                        elif task.state == "FAILED":
                            self.J["sim_status"] = message_numbers.TASK_FAILED
                            halt_job_sequence = True
                            break
                        else:
                            self.log.warning("Unknown task failure")
                            self.J["sim_status"] = message_numbers.TASK_FAILED
                            halt_job_sequence = True
                            break
                    elif task.runtime > job.setup.timeout:
                        self.log.warning("Task Timed out, aborting Job chain")
                        self.J["sim_status"] = message_numbers.WORKER_KILL_ON_TIMEOUT
                        task.kill()  # Timeout
                        halt_job_sequence = True
                        break

                if executor_arguments.get("auto_assign_gpus") and self.log.isEnabledFor(
                    logging.DEBUG
                ):
                    from libensemble.tools.test_support import check_gpu_setting

                    self.log.debug(
                        check_gpu_setting(
                            task, assert_setting=False, print_setting=True
                        )
                    )
            else:
                raise NotImplementedError(
                    f"Execution mode for job type: {job.code} was not handled"
                )

            # Don't let this job's GPU restriction leak into later jobs in the chain
            restore_env(gpu_env)

            if halt_job_sequence:
                break

            if job.setup.output_distribution:
                self.switchyard = rsopt.conversion.create_switchyard(
                    job.output_distribution, job.code
                )
                self.J["switchyard"] = self.switchyard

            # Run postprocess
            if job.setup.postprocess:
                job.get_postprocess_function(self.J)

        if (
            self.J["sim_status"] == message_numbers.WORKER_DONE
            and not halt_job_sequence
        ):
            # Use objective function if given
            if self.objective_function:
                val = self.objective_function(self.J)
                output = format_evaluation(self.sim_specs, val)
                self.log.info("val: {}, output: {}".format(val, output))
            else:
                # If only serial python was run then objective_function doesn't need to be defined
                try:
                    output = format_evaluation(self.sim_specs, f)
                except NameError as e:
                    print(e)
                    print(
                        "An objective function must be defined if final Job is is not Python"
                    )
        else:
            # TODO: Temporary penalty. Need to add a way to adjust this.
            self.log.warning("Penalty was used because result could not be evaluated")
            output = format_evaluation(self.sim_specs, _PENALTY)

        return output, persis_info, self.J["sim_status"]
