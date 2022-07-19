active_env = None

def get_mpi_environment():
    global active_env

    # Test for mpi4py install
    try:
        import mpi4py
        mpi4py.rc.initialize = False
        from mpi4py import MPI
    except ModuleNotFoundError:
        # mpi4py not installed so it can't be used
        return None

    # If we already ran this process, return the active environment
    if active_env:
        return active_env

    from inspect import currentframe, getframeinfo
    frameinfo = getframeinfo(currentframe())
    print(f"Initializing MPI from {frameinfo.filename}:L{frameinfo.lineno}", flush=True)

    #import faulthandler
    #import sys
    #faulthandler.enable(file=sys.stderr, all_threads=True)

    # Test MPI intialization in another thread
    import subprocess
    import os
    import rsopt
    fname = os.path.dirname(rsopt.__file__) + "/__main__.py"
    pp = subprocess.run(["python", fname])
    
    if pp.returncode != 0:
        return None

    # Should already be initialized
    # MPI.Init()

    if not MPI.COMM_WORLD.Get_size() - 1:
        # MPI not being used
        # (if user did start MPI with size 1 this would be an illegal configuration since: main + 1 worker = 2 ranks)
        return None

    nworkers = MPI.COMM_WORLD.Get_size() - 1
    is_manager = MPI.COMM_WORLD.Get_rank() == 0
    mpi_environment = {'mpi_comm': MPI.COMM_WORLD, 'comms': 'mpi', 'nworkers': nworkers, 'is_manager': is_manager}

    # Save global environment
    active_env = mpi_environment

    return mpi_environment
