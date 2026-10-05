import logging
import os
from libensemble.resources.resources import Resources


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
