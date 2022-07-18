
def get_mpi_environment():
    try:
        import mpi4py
        mpi4py.rc.initialize = False
    except ModuleNotFoundError:
        # mpi4py not installed so it can't be used
        return

    from mpi4py import MPI
    MPI.Init()

    if not MPI.COMM_WORLD.Get_size() - 1:
        # MPI not being used
        # (if user did start MPI with size 1 this would be an illegal configuration since: main + 1 worker = 2 ranks)
        return

    nworkers = MPI.COMM_WORLD.Get_size() - 1
    is_manager = MPI.COMM_WORLD.Get_rank() == 0
    mpi_environment = {'mpi_comm': MPI.COMM_WORLD, 'comms': 'mpi', 'nworkers': nworkers, 'is_manager': is_manager}

    return mpi_environment
