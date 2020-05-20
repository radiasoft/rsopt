import yaml
import os, time, subprocess, uuid
import numpy as np
import h5py as h5


def create_settings_file(path, sim_id, base_file, new_settings):
    """
    Make a new TEC description file based on new settings and the 'tec_start.yaml' base file.
    Return the UUID generated, unique identifier for the file.
    """
    base_file = yaml.safe_load(open(base_file, 'r'))

    b, h, r = new_settings

    base_file['tec']['magnetic_field'] = float(b)
    base_file['tec']['grid_height'] = float(h)
    base_file['tec']['strut_width'] = float(base_file['tec']['strut_height'] / r)

    new_file = sim_id + '.yaml'
    yaml.dump(base_file, open(os.path.join(path, new_file), 'w'))


def get_optimization_parameters(path):
    parameters = yaml.safe_load(open(path, 'r'))
    b = float(parameters['tec']['magnetic_field'])
    h = float(parameters['tec']['grid_height'])
    r = float(parameters['tec']['strut_height'] / parameters['tec']['strut_width'])

    return b, h, r


def get_efficiency(path, sim_id, penalty=-10.):
    """
    Path to .h5 file with efficiency data. Will check for sufficiently completed simulation and
    return the efficiency or a preset penalty value
    if the simulation did not complete enough to generate a useful efficiency calculation.

    :path: (str) Path to base output directory. Will contain diag directories.
    :penalty: (float) Value to return if simulation did not complete (`path` must be loadable or an error occurs).

    Return (float) efficiency
    """
    filename = 'efficiency_id_' + sim_id + '.h5'
    diag_path = 'diag_id_' + sim_id
    file_path = os.path.join(path, diag_path, filename)
    datafile = h5.File(file_path, 'r')
    if datafile.attrs['complete'] == 0 or datafile.attrs['complete'] == 3:
        # Simulation returned a meaningful result
        efficiency = datafile['efficiency'].attrs['eta']
    else:
        # Simulation did not go far enough to calculate a meaningful efficiency
        # Supply large penalty
        efficiency = penalty

    return efficiency