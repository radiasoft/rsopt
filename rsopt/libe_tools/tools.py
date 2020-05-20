
def create_empty_persis_info(libE_specs):
    """
    Create `persis_info` for libEnsemble if no persistent data needs to be transfered.
    :param libE_specs: `libE_specs` datastructure.
    :return:
    """
    nworkers = libE_specs['nworkers']
    persis_info = {i: {'worker_num': i} for i in range(1, nworkers+1)}

    return persis_info