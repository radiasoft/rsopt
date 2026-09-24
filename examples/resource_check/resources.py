#!/usr/bin/env python3
"""
mpi_host_info.py

Print identification information for the machine and MPI runner stats using mpi4py.

Usage examples:
  python mpi_host_info.py
  mpirun -np 8 python mpi_host_info.py
  srun -n 16 python mpi_host_info.py
"""

from __future__ import annotations

import getpass
import os
import platform
import socket
import sys
import time
from collections import Counter
from typing import Any, Dict, Optional

from mpi4py import MPI


def _try_import_psutil():
    try:
        import psutil  # type: ignore
        return psutil
    except Exception:
        return None


def _safe_loadavg() -> Optional[tuple[float, float, float]]:
    try:
        return os.getloadavg()  # Unix only
    except Exception:
        return None


def _fmt_bytes(n: Optional[int]) -> str:
    if n is None:
        return "N/A"
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    x = float(n)
    for u in units:
        if x < 1024.0 or u == units[-1]:
            return f"{x:.2f} {u}"
        x /= 1024.0
    return f"{n} B"


def _collect_host_info(psutil) -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    info["hostname"] = socket.gethostname()
    try:
        info["fqdn"] = socket.getfqdn()
    except Exception:
        info["fqdn"] = "N/A"
    info["platform"] = platform.platform()
    info["system"] = platform.system()
    info["release"] = platform.release()
    info["version"] = platform.version()
    info["machine"] = platform.machine()
    info["processor"] = platform.processor() or "N/A"

    info["python"] = sys.version.replace("\n", " ")
    info["executable"] = sys.executable
    info["user"] = getpass.getuser()
    info["uid"] = os.getuid() if hasattr(os, "getuid") else "N/A"
    info["gid"] = os.getgid() if hasattr(os, "getgid") else "N/A"
    info["cwd"] = os.getcwd()

    # CPU core counts
    info["cpu_count_logical"] = os.cpu_count()
    if psutil is not None:
        try:
            info["cpu_count_physical"] = psutil.cpu_count(logical=False)
        except Exception:
            info["cpu_count_physical"] = "N/A"
    else:
        info["cpu_count_physical"] = "N/A"

    # Memory
    if psutil is not None:
        try:
            vm = psutil.virtual_memory()
            info["mem_total"] = vm.total
            info["mem_available"] = vm.available
        except Exception:
            info["mem_total"] = None
            info["mem_available"] = None
    else:
        info["mem_total"] = None
        info["mem_available"] = None

    # Load averages
    info["loadavg"] = _safe_loadavg()
    return info


def _collect_mpi_env_hints() -> Dict[str, str]:
    """
    Common launcher variables (best-effort; varies by MPI/launcher).
    """
    keys = [
        # Open MPI
        "OMPI_COMM_WORLD_RANK",
        "OMPI_COMM_WORLD_SIZE",
        "OMPI_COMM_WORLD_LOCAL_RANK",
        "OMPI_COMM_WORLD_NODE_RANK",
        # MPICH / Intel MPI / Hydra
        "PMI_RANK",
        "PMI_SIZE",
        "PMI_LOCAL_RANK",
        "PMIX_RANK",
        # SLURM
        "SLURM_JOB_ID",
        "SLURM_PROCID",
        "SLURM_LOCALID",
        "SLURM_NTASKS",
        "SLURM_NODEID",
        "SLURM_JOB_NODELIST",
        "SLURM_CLUSTER_NAME",
        # Generic
        "MPI_LOCALRANKID",
        "MPI_LOCALNRANKS",
        "HOSTNAME",
    ]
    out: Dict[str, str] = {}
    for k in keys:
        v = os.environ.get(k)
        if v is not None:
            out[k] = v
    return out


def _print_kv(title: str, kv: Dict[str, Any], indent: str = "  ") -> None:
    print(title)
    for k in sorted(kv.keys()):
        v = kv[k]
        if k in ("mem_total", "mem_available"):
            print(f"{indent}{k}: {_fmt_bytes(v)}")
        elif k == "loadavg" and isinstance(v, tuple):
            print(f"{indent}{k}: {v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f}")
        else:
            print(f"{indent}{k}: {v}")
    print()


def main(dummy: int = 0) -> None:
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Rank-local info
    psutil = _try_import_psutil()
    host_info = _collect_host_info(psutil)
    mpi_env = _collect_mpi_env_hints()

    # MPI identity
    proc_name = MPI.Get_processor_name()
    try:
        libver = MPI.Get_library_version().strip()
    except Exception:
        libver = "N/A"

    # Gather node names for inventory
    all_proc_names = comm.allgather(proc_name)
    node_counts = Counter(all_proc_names)

    # ranks-per-node (map node -> list of ranks)
    rank_map = comm.allgather((proc_name, rank))
    node_to_ranks: Dict[str, list[int]] = {}
    for n, r in rank_map:
        node_to_ranks.setdefault(n, []).append(r)
    for n in node_to_ranks:
        node_to_ranks[n].sort()

    # Simple MPI timing signals
    comm.Barrier()
    t0 = MPI.Wtime()
    comm.Barrier()
    barrier_s = MPI.Wtime() - t0

    # Allreduce timing and correctness check
    x = float(rank + 1)
    comm.Barrier()
    t1 = MPI.Wtime()
    ssum = comm.allreduce(x, op=MPI.SUM)
    allreduce_s = MPI.Wtime() - t1
    expected = float(size * (size + 1) / 2)

    # Print: per-rank details, ordered by rank
    for r in range(size):
        comm.Barrier()
        if r != rank:
            continue

        print("=" * 72)
        print(f"MPI Rank {rank}/{size-1}")
        print(f"Processor name (MPI): {proc_name}")
        print(f"MPI library: {libver}")
        print()

        _print_kv("Host identification:", host_info)
        _print_kv("MPI/launcher environment hints (best-effort):", mpi_env)

        print("MPI timing signals (per-rank):")
        print(f"  barrier_time_s:   {barrier_s:.6e}")
        print(f"  allreduce_time_s: {allreduce_s:.6e}")
        print(f"  allreduce_sum:    {ssum:.6f} (expected {expected:.6f})")
        print()

    # Print: one-time world summary on rank 0
    comm.Barrier()
    if rank == 0:
        print("=" * 72)
        print("MPI World summary (rank 0):")
        print(f"  world_size: {size}")
        print(f"  unique_nodes: {len(node_counts)}")
        print("  node_inventory:")
        for node in sorted(node_counts.keys()):
            ranks = node_to_ranks.get(node, [])
            print(f"    {node}: {node_counts[node]} ranks; ranks={ranks}")
        print()

    comm.Barrier()


if __name__ == "__main__":
    main()

