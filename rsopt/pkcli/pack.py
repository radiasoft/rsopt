import rsopt.parse as parse
import modulefinder
import tarfile
import pathlib
import os
import typer

app = typer.Typer()

def _get_local_modules(script_name):
    # return a list of modules used defined in the same directory as `script_name` (including `script_name`)
    file_list = []
    finder = modulefinder.ModuleFinder(path=['.', ])
    finder.run_script(script_name)
    for name, mod in finder.modules.items():
        if mod.__file__:  # Skips standard library imports
            # Already assume we get only local files so truncate off any path info.
            file_list.append(pathlib.Path(mod.__file__).name)

    return file_list


def _get_processing(job):
    # return pre/post processing scripts and local dependencies (if any)
    file_list = []
    for attr in ['preprocess', 'postprocess']:
        if job.setup.get(attr):
            file_name = job.setup.get(attr)[0]
            files = _get_local_modules(file_name)
            file_list.extend(files)

    return file_list


def _get_file_list_from_model(model, code_name, input_file_path):
    import sirepo.sim_data
    from sirepo.template import lattice

    # Use same path as configuration file when packing
    model_path = pathlib.Path(input_file_path).parents[0]
    # Get input and lattice if exists
    file_list = [model_path.joinpath(model['_SimData__source'].basename), ]

    if hasattr(model._SimData__adapter, '_run_setup'):
        lattice_file = model._SimData__adapter._run_setup(model).lattice
        file_list.append(model_path.joinpath(lattice_file))

    # Get all supporting files
    _sim_data, _, _schema = sirepo.sim_data.template_globals(code_name)
    files = lattice.LatticeUtil(model, _schema).iterate_models(
        lattice.InputFileIterator(_sim_data, update_filenames=False),).result
    file_list.extend([model_path.joinpath(ff) for ff in files])

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
        files = _get_file_list_from_model(m, job.code, job.setup['input_file'])
        file_list.extend(files)

    files = _get_processing(job)
    file_list.extend(files)

    # return file paths as string to match against anything passed to ignore list
    return [str(f) for f in file_list]


def _get_files_from_options(config):
    # return all files defined in options
    file_list = []
    if config.options.sym_links:
        file_list.extend(config.options.sym_links)
    if config.options.objective_function:
        files = _get_local_modules(config.options.objective_function[0])
        file_list.extend(files)

    # return file paths as string to match against anything passed to ignore list
    return [str(f) for f in file_list]


def _create_tar(name, file_list):
    tarname = f'{name}.tar.gz'
    tar = tarfile.open(tarname, 'w:gz')
    for file in file_list:
        print("Adding file to tarball: {}".format(file))
        tar.add(file)

    tar.close()

    return tarname


@app.command()
def configuration(config: str, ignore=None, add=None):
    """Create a tarball of all configuration file dependencies.

    Locally defined Python modules will be included but not library files.

    :param config: (str) Name of configuration file to use
    :param ignore: Optional. Files that should not be included in tarball.
    :param add: Optional. Files to include that are not automatically detected from the configuration file.
    :return: None
    """

    if not ignore:
        ignore = []

    file_list = [config,]
    config_yaml = parse.read_configuration_file(config)
    _config = parse.parse_yaml_configuration(config_yaml)

    for job in _config.jobs:
        files = _get_files_from_job(job)
        ignore.extend(job.get_ignored_files(with_path=True))
        file_list.extend(files)

    files = _get_files_from_options(_config)
    file_list.extend(files)
    # remove any duplicate items
    file_list = set(file_list)

    if ignore:
        for file in ignore:
            if file in file_list:
                file_list.remove(file)
            else:
                print(f'File: {file} is not being used by rsopt configuration. Nothing to ignore.')
    if add:
        for file in add:
            if file not in file_list:
                file_list.add(file)
            else:
                print(f'File: {file} already found in rsopt configuration. Skipping add.')

    tar_name = os.path.splitext(config)[0]
    create_filename = _create_tar(tar_name, file_list)
    print(f"Created tarball: {create_filename}")

