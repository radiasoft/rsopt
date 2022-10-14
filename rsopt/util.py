import re
import os
import logging
import numpy as np
import pickle
from libensemble.tools import save_libE_output
from .mpi import get_mpi_environment

SLURM_PREFIX = 'nid'


def _expand_idx(idx):
    if idx.startswith('['):
        idx = idx[1:-1]
    idx_parts = idx.split(',')
    indexes = []
    for part in idx_parts:
        if "-" in part:
            # Assumes len(start) == len(stop)
            start, stop = part.split('-', 2)
            length = len(start)
            indexes.extend(range(int(start), int(stop)+1))
            indexes = [str(i).zfill(length) for i in indexes]
        else:
            indexes.append(part)
    indexes.sort(key=int)
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

    index_pat = re.compile(r'((nid(\w*))(\d+|\[[\d\,\-]+\]),?)')
    for match in index_pat.finditer(nodelist_string):
        prefix = match.group(2)
        node_type = match.group(3)
        idx = match.group(4)
        idx_list = _expand_idx(idx)
        return _expand_nodestr(prefix, idx_list)
    else:
        return []


def return_used_nodes():
    """Returns all used processor names to rank 0 or an empty list if MPI not used. For ranks != 0  returns None."""
    if not get_mpi_environment():
        return []

    from mpi4py import MPI
    
    rank = MPI.COMM_WORLD.Get_rank()
    name = MPI.Get_processor_name()
    all_names = MPI.COMM_WORLD.gather(name, root=0)

    if rank == 0:
        return all_names
    else:
        return None


def return_unused_node():
    """Check where MPI processes are running and return the first unused node from SLURM nodelist"""
    try:
        nodelist_string = os.environ['SLURM_JOB_NODELIST']
    except KeyError:
        raise KeyError('Cannot find SLURM_JOB_NODELIST. Shifter execution may not be available.')
    allocated_nodes = return_nodelist(nodelist_string)
    used_nodes = return_used_nodes()

    if used_nodes is None:
        # Catches rank != 0 if MPI used
        return None
    
    for node in allocated_nodes:
        if node not in used_nodes:
            return node
    else:
        raise SystemError("Could not find an unused node")


def broadcast(data, root_rank=0):
    """broadcast, or don't bother"""
    if not get_mpi_environment():
        return data

    from mpi4py import MPI

    if MPI.COMM_WORLD.Get_size() == 1:
        return data

    return MPI.COMM_WORLD.bcast(data, root=root_rank)


def save_final_history(config_filename, config, H, persis_info, nworkers, message):
    if config.options.output_file:
        filename = config.options.output_file
        _libe_save(H, persis_info, message, filename)
    else:
        filename = os.path.splitext(config_filename)[0]
        history_file_name = "H_sample_" + filename + ".npy"
        save_libE_output(H, persis_info, history_file_name, nworkers, mess=message)


def _libe_save(H, persis_info, mess, filename):
    # copy of the file save portion of libensemble.tools.save_libE_output, but with full control of save filename
    status_mess = ' '.join(['------------------', mess, '-------------------'])
    print('{}\nSaving results to file: {}'.format(status_mess, filename))
    np.save(filename, H)

    with open(filename + ".pickle", "wb") as f:
        pickle.dump(persis_info, f)
