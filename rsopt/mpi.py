import os
import subprocess
from inspect import currentframe, getframeinfo
import rsopt

__active_env = None

def get_mpi_environment():
    """Checks MPI environment and whether or not MPI is initialized

    Params:
        None

    Returns:
        None if mpi is unavailable; else a dict representing the active MPI environment"""
    global __active_env

    # Test for mpi4py install
    try:
        import mpi4py
        mpi4py.rc.initialize = False
        from mpi4py import MPI
    except ModuleNotFoundError:
        # mpi4py not installed so it can't be used
        __active_env = "no_mpi"

    if __active_env == "no_mpi":
        return None

    # If we already ran this process and have an environment, return the active environment
    if __active_env:
        return __active_env
    
    frameinfo = getframeinfo(currentframe())
    print(f"Initializing MPI from {frameinfo.filename}:L{frameinfo.lineno}", flush=True)

    #import faulthandler
    #import sys
    #faulthandler.enable(file=sys.stderr, all_threads=True)

    # Test MPI intialization in another thread
    fname = os.path.dirname(rsopt.__file__) + "/__main__.py"
    pp = subprocess.run(["python", fname])
    
    if pp.returncode != 0:
        __active_env = "no_mpi"
        return None

    if not MPI.COMM_WORLD.Get_size() - 1:
        # MPI not being used
        # (if user did start MPI with size 1 this would be an illegal configuration since: main + 1 worker = 2 ranks)
        __active_env = "no_mpi"
        return None

    nworkers = MPI.COMM_WORLD.Get_size() - 1
    is_manager = MPI.COMM_WORLD.Get_rank() == 0
    mpi_environment = {'mpi_comm': MPI.COMM_WORLD, 'comms': 'mpi', 'nworkers': nworkers, 'is_manager': is_manager}

    # Save global environment
    __active_env = mpi_environment

    return mpi_environment
