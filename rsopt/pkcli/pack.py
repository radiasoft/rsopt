import rsopt.parse as parse
import sirepo.sim_data  # Can't run import sirepo and call sirepo.sim_data. ??
import modulefinder
import tarfile
import os
from sirepo.template import lattice

def _get_local_modules(script_name):
    # return a list of modules used defined in the same directory as `script_name` (including `script_name`)
    file_list = []
    finder = modulefinder.ModuleFinder(path=['.', ])
    finder.run_script(script_name)
    for name, mod in finder.modules.items():
        if mod.__file__:  # Skips standard library imports
            file_list.append(mod.__file__)

    return file_list

def _get_processing(job):
    # return pre/post processing scripts and local dependencies (if any)
    file_list = []
    for attr in ['pre_process', 'post_process']:
        if job.__getattribute__(attr):
            file_name = job.__getattribute__(attr)[0]
            files = _get_local_modules(file_name)
            file_list.extend(files)

    return file_list


def _get_file_list_from_model(model, code_name):
    # Get input and lattice if exists
    file_list = [model['_SimData__source'].basename, ]
    try:
        lattice_file = model._SimData__adapter._lattice_path('', model)
        file_list.append(lattice_file)
    except AttributeError:
        pass

    # Get all supporting files
    _sim_data, _, _schema = sirepo.sim_data.template_globals(code_name)
    files = lattice.LatticeUtil(model, _schema).iterate_models(
        lattice.InputFileIterator(_sim_data, update_filenames=False),).result
    file_list.extend(files)

    return file_list

def _get_files_from_job(job):
    # return all files defined in a job
    file_list = []

    if job.code == 'user' or job.code == 'genesis':
        raise NotImplementedError('Collection of files from `{}` jobs not implemented'.format(job.code))
    elif job.code == 'python':
        files = _get_local_modules(job.setup['input_file'])
        file_list.extend(files)
    else:
        m = job._setup.input_file_model
        files = _get_file_list_from_model(m, job.code)
        file_list.extend(files)

    files = _get_processing(job)
    file_list.extend(files)

    return file_list

def _get_files_from_options(config):
    # return all files defined in options
    file_list = []
    if config.options.sym_links:
        file_list.extend(config.options.sym_links)
    if config.options.objective_function:
        files = _get_local_modules(config.options.objective_function[0])
        file_list.extend(files)

    return file_list


def _create_tar(name, file_list):
    tarname = f'{name}.tar.gz'
    tar = tarfile.open(tarname, 'w:gz')
    for file in file_list:
        print("Adding file to tarball: {}".format(file))
        tar.add(file)

    tar.close()

    return tarname


def configuration(config, ignore=None, add=None):
    """
    Packs all run files used by the configuration file into a tarball.
    Locally defined Python modules will be included.

    :param config: (str) Name of configuration file to use
    :param ignore: Optional. Files that should not be included in tarball.
    :param add: Optional. Files to include that are not automatically detected from the configuration file.
    :return: None
    """
    file_list = [config,]
    config_yaml = parse.read_configuration_file(config)
    _config = parse.parse_yaml_configuration(config_yaml)

    for job in _config.jobs:
        files = _get_files_from_job(job)
        file_list.extend(files)

    files = _get_files_from_options(_config)
    file_list.extend(files)

    if ignore:
        for file in ignore:
            if ignore in file_list:
                file_list.remove(file)
            else:
                print(f'File: {file} is not being used by rsopt configuration. Nothing to ignore.')
    if add:
        for file in add:
            if file not in file_list:
                file_list.append(file)
            else:
                print(f'File: {file} already found in rsopt configuration. Skipping add.')

    tar_name = os.path.splitext(config)[0]
    create_filename = _create_tar(tar_name, file_list)
    print(f"Created tarball: {create_filename}")

