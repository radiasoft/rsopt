import re, os

SLURM_PREFIX = 'nid'


def _expand_idx(idx):
    if idx.startswith('['):
        idx = idx[1:-1]
    idx_parts = idx.split(',')
    indexes = []
    for part in idx_parts:
        if "-" in part:
            start, stop = part.split('-', 2)
            indexes.extend(range(int(start), int(stop)+1))
        else:
            indexes.append(int(part))
    indexes.sort()
    return indexes


def _expand_nodestr(nodestri, idx_list):
    return [nodestri + str(idx) for idx in idx_list]


def return_nodelist(nodelist_string):
    """
    Given a nodelist as a string return a list of all nodes in sequential order.
    Node names include prefix.

    If `nodelist_string` does not contain any recognized node names an empty list is returned.

    :param nodelist_string: (str) Nodelist from SLURM environment variables: SLURM_JOB_NODELIST or SLURM_NODELIST
    :return: list
    """

    index_pat = re.compile(r'((nid(\w+))(\d+|\[[\d\,\-]+\]),?)')
    for match in index_pat.finditer(nodelist_string):
        prefix = match.group(2)
        node_type = match.group(3)
        idx = match.group(4)
        idx_list = _expand_idx(idx)
        return _expand_nodestr(prefix, idx_list)
    else:
        return []


def return_used_nodes():
    """Returns all used processor names to rank 0 and an empty list elsewhere"""
    try:
        from mpi4py import MPI
    except ModuleNotFoundError:
        # If MPI not being used to start rsopt then no nodes will have srun executed yet
        return []

    rank = MPI.COMM_WORLD.Get_rank()
    name = MPI.Get_processor_name()
    all_names = MPI.COMM_WORLD.gather(name, root=0)

    if rank == 0:
        return all_names
    else:
        return []


def return_unused_node():
    """Check where MPI processes are running and return the first unused node from SLURM nodelist"""
    nodelist_string = os.environ['SLURM_JOB_NODELIST']
    allocated_nodes = return_nodelist(nodelist_string)
    used_nodes = return_used_nodes()

    if len(used_nodes) == 0:
        return None

    for node in allocated_nodes:
        if node not in used_nodes:
            return node
    else:
        raise SystemError("Could not find an unused node")


def broadcast(data, root_rank=0):
    """broadcast, or don't bother"""
    try:
        from mpi4py import MPI
    except ModuleNotFoundError:
        # If MPI not available for import then assume it isn't needed
        return data

    if MPI.COMM_WORLD.Get_size() == 1:
        return data

    return MPI.COMM_WORLD.bcast(data, root=root_rank)





