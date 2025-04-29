import importlib.machinery
import importlib.resources
import importlib.util
import numpy as np
import os
import pathlib
import pickle
import re
import shutil
import sys


def run_path_as_module(fname):
    """Runs ``fname`` in a module.

    Args:
        fname (str or pathlib.Path): file to be exec'd

    Returns:
        module: imported file as a module
    """
    fname = str(fname)
    mn = pathlib.Path(fname).name.replace(".", "_")
    m = importlib.util.module_from_spec(importlib.machinery.ModuleSpec(mn, None))
    with open(fname, "rt") as f:
        code = compile(f.read(), fname, "exec")
    exec(code, m.__dict__)
    return m


def package_data_path() -> pathlib.Path:
    package_data_directory = 'package_data'
    rsopt_package_data = importlib.resources.files('rsopt') / package_data_directory

    return rsopt_package_data


SLURM_PREFIX = 'nid'
_FINAL_LOGS = ('ensemble.log', 'libE_stats.txt')

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
    try:
        from mpi4py import MPI
    except ModuleNotFoundError:
        # If MPI not available for import then assume it isn't needed
        return data

    if MPI.COMM_WORLD.Get_size() == 1:
        return data

    return MPI.COMM_WORLD.bcast(data, root=root_rank)


def save_final_history(configuration, loaded_config_path, H, persis_info, message) -> (str, str):
    if configuration.options.output_file:
        filename = configuration.options.output_file

        return save_libE_output(H, persis_info, filename, message, custom_filename=True)
    else:
        filename = pathlib.Path(loaded_config_path).stem
        history_file_name = "H_" + filename

        return save_libE_output(H, persis_info, history_file_name, configuration.options.nworkers, mess=message)


def save_libE_output(H, persis_info, calling_file, nworkers, mess="Run completed", custom_filename=False) -> (str, str):
    """Writes out history array and persis_info to files.

    Args:
        H: (numpy.ndarray) Structured NumPy array with libEnsemble history.
        persis_info: (dict) Dictionary with libEnsemble worker persis info.
        calling_file: (str) Name of configuration file or a custom file name.
        nworkers: (int or str) Number of workers used.
        mess: (str) Message printed at save.
        custom_filename: (bool) Treat `calling_file` as custom filename. In this case the usual name mangling for
         the history and persis_info files is not performed. They will be saved as:
         $calling_file.npy and $calling_file.pickle.

    Returns:
        NumPy save history filename (str), persis_info pickle filename (str)
    """

    name = pathlib.Path(calling_file).stem
    prob_str = "length-" + str(len(H)) + "_evals-" + str(sum(H["sim_ended"])) + "_workers-" + str(nworkers)
    if custom_filename:
        h_filename = calling_file
        p_filename = calling_file
    else:
        h_filename = name + "_history_" + prob_str
        p_filename = name + "_persis_info_" + prob_str

    status_mess = " ".join(["------------------", mess, "-------------------"])
    print("{}\nSaving results to file: {}".format(status_mess, h_filename))
    np.save(h_filename, H)

    with open(p_filename + ".pickle", "wb") as f:
        pickle.dump(persis_info, f)

    return h_filename + ".npy", p_filename + ".pickle"


def get_objective_function(obj_definition: tuple[str, str] or None) -> callable:
    """Returns the function object from module.

    Args:
        obj_definition: (list or tuple) [path to module (str), function name (str)]

    Returns: (callable) function

    """

    # import the objective function if given
    if obj_definition is not None:
        module_path, function_name = obj_definition
        sys.path.append(os.getcwd())
        module = run_path_as_module(module_path)
        function = getattr(module, function_name)
        return function

    return None


def copy_final_logs(config_filename: str,
                    options: "rsopt.configuration.options.Options",
                    history_filename: str or None = None):
    run_dir = pathlib.Path(options.run_dir)
    for filename in _FINAL_LOGS + (config_filename,):
        filename = pathlib.Path(filename)
        if filename.exists():
            shutil.copy(filename, run_dir.joinpath(filename.name))
        else:
            print(f"Could not find {filename} at run end. Will not be copied to run directory.")
    if history_filename:
        history_path = pathlib.Path(history_filename)
        if history_path.exists():
            shutil.copy(history_path, run_dir.joinpath(history_path.name))
        else:
            print(f"Could not find {history_filename} at run end. Will not be copied to run directory.")
