"""GPU smoke test: report which GPU(s) this process sees, then load it for about 10 s."""
import os
import socket
import subprocess
import time

import torch

DURATION = 10.0  # seconds of load
MATRIX_SIZE = 8192

# Environment variables that MPI launchers / schedulers use for rank IDs.
# libEnsemble's GPU assignment works by setting the device-visibility variables.
RANK_VARS = ['OMPI_COMM_WORLD_RANK', 'PMI_RANK', 'PMIX_RANK', 'SLURM_PROCID', 'PALS_RANKID']
LOCAL_RANK_VARS = ['OMPI_COMM_WORLD_LOCAL_RANK', 'MPI_LOCALRANKID', 'PMI_LOCAL_RANK',
                   'SLURM_LOCALID', 'PALS_LOCAL_RANKID']
DEVICE_VARS = ['CUDA_VISIBLE_DEVICES', 'ROCR_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES',
               'ZE_AFFINITY_MASK', 'SLURM_STEP_GPUS', 'SLURM_JOB_GPUS']


def _first_env(names, default=None):
    for name in names:
        if name in os.environ:
            return int(os.environ[name])
    return default


def report():
    rank = _first_env(RANK_VARS, 0)
    local_rank = _first_env(LOCAL_RANK_VARS, 0)
    tag = f'[host={socket.gethostname()} pid={os.getpid()} rank={rank} local_rank={local_rank}]'

    print(f'{tag} GPU environment:')
    for name in DEVICE_VARS:
        print(f'{tag}   {name}={os.environ.get(name, "<unset>")}')

    if not torch.cuda.is_available():
        raise RuntimeError(f'{tag} torch sees no GPU')

    n = torch.cuda.device_count()
    print(f'{tag} torch sees {n} device(s):')
    for i in range(n):
        p = torch.cuda.get_device_properties(i)
        print(f'{tag}   [{i}] {p.name}  {p.total_memory / 2**30:.1f} GiB')

    # If several ranks share the visible devices, spread them out by local rank
    device = local_rank % n
    torch.cuda.set_device(device)
    print(f'{tag} using torch device {device}: {torch.cuda.get_device_name(device)}')

    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,pci.bus_id,name',
                              '--format=csv,noheader'], capture_output=True, text=True, timeout=10)
        print(f'{tag} nvidia-smi (visible to this process):\n{out.stdout.strip()}')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return tag, device


def burn(tag, device, duration=DURATION):
    a = torch.randn(MATRIX_SIZE, MATRIX_SIZE, device=device)
    b = torch.randn(MATRIX_SIZE, MATRIX_SIZE, device=device)
    torch.cuda.synchronize()

    iters = 0
    start = time.time()
    while time.time() - start < duration:
        for _ in range(10):
            c = a @ b
        torch.cuda.synchronize()
        iters += 10
    elapsed = time.time() - start

    tflops = 2 * MATRIX_SIZE**3 * iters / elapsed / 1e12
    print(f'{tag} done: {iters} matmuls in {elapsed:.1f} s  (~{tflops:.1f} TFLOP/s fp32), '
          f'checksum={c[0, 0].item():.4f}')


def gpu_test(*args, **kwargs):
    """Entry point for rsopt Python jobs."""
    tag, device = report()
    burn(tag, device)


if __name__ == '__main__':
    gpu_test()