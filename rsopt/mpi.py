from libensemble.resources import mpi_resources


def get_mpi_environment():
    # If using openmpi it is not safe to `from mpi4py import MPI` this alone will move you to working in a nested
    # environment. Even if MPI.COMM_WORLD.Get_size() use of an MPIExecutor will fail (potentially without an error
    # message) you will just get error code = 1 from the subprocess that tried to use mpirun.

    if mpi_resources.get_MPI_variant() == "openmpi":
        print("openmpi use detected. MPI communication will not be used.")
        return

    try:
        from mpi4py import MPI
    except ModuleNotFoundError:
        # mpi4py not installed so it can't be used
        return

    if not MPI.COMM_WORLD.Get_size() - 1:
        # MPI not being used
        # (if user did start MPI with size 1 this would be an illegal configuration since: main + 1 worker = 2 ranks)
        return

    nworkers = MPI.COMM_WORLD.Get_size() - 1
    is_manager = MPI.COMM_WORLD.Get_rank() == 0
    mpi_environment = {'mpi_comm': MPI.COMM_WORLD, 'comms': 'mpi', 'nworkers': nworkers, 'is_manager': is_manager}

    return mpi_environment