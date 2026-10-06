"""End-to-end regression test over the packaged examples in `example_registry.yml`.

Each example's files are copied into a temporary directory and the configuration is run through the same CLI
function a user would call. The best objective value found must match the `result` recorded in the registry.
Examples whose optional packages or executables are not available are skipped.
"""
import atexit
import importlib.util
import os
import pathlib
import shutil
import numpy as np
import pytest
from ruamel.yaml import YAML
from rsopt import EXAMPLE_SYMLINK, EXAMPLE_REGISTRY
from rsopt import parse
from rsopt.configuration.options import SUPPORTED_OPTIONS
from rsopt.pkcli import optimize, sample

_EXAMPLES = YAML(typ='safe').load(pathlib.Path(EXAMPLE_REGISTRY))['examples']

# Optional Python packages and executables each example needs beyond rsopt's required dependencies
REQUIREMENTS = {
    'quickstart_example': {'modules': ['nlopt'], 'executables': []},
    'python_dfols_example': {'modules': ['dfols'], 'executables': []},
    'python_aposmm_example': {'modules': ['nlopt'], 'executables': []},
    'elegant_matching_parallel_execution_example': {'modules': ['sirepo'], 'executables': ['Pelegant', 'mpiexec']},
    'pybobyqa_himmelblau_example': {'modules': ['pybobyqa'], 'executables': []},
}

RUN_COMMANDS = {
    'sample': sample.configuration,
    'optimize': optimize.configuration,
}


def _missing_requirements(name):
    requirements = REQUIREMENTS[name]
    missing = [m for m in requirements['modules'] if importlib.util.find_spec(m) is None]
    missing += [e for e in requirements['executables'] if shutil.which(e) is None]
    return missing


def _example_params():
    for name in _EXAMPLES:
        missing = _missing_requirements(name) if name in REQUIREMENTS else []
        marks = [pytest.mark.skip(reason=f'missing: {", ".join(missing)}')] if missing else []
        yield pytest.param(name, marks=marks, id=name)


def copy_example_files(example, directory):
    # Registry paths may be nested under the packaged examples directory, but every example expects
    # its files to sit alongside each other in the working directory, so copy them out by basename.
    file_list = []
    for source in example['files']:
        target = pathlib.Path(directory) / pathlib.Path(source).name
        shutil.copyfile(pathlib.Path(EXAMPLE_SYMLINK) / source, target, follow_symlinks=True)
        file_list.append(target.name)

    return file_list


def test_requirements_cover_registry():
    assert set(REQUIREMENTS) == set(_EXAMPLES)


@pytest.mark.parametrize('name', list(_example_params()))
def test_example(name, tmp_path, monkeypatch):
    example = _EXAMPLES[name]
    monkeypatch.chdir(tmp_path)
    # The registry requires the configuration file to be listed last
    config_filename = copy_example_files(example, tmp_path)[-1]
    # Run with the command matching the configured software rather than the registry's job_type
    software = parse.read_configuration_file(config_filename)['options']['software']

    H, _, _ = RUN_COMMANDS[getattr(SUPPORTED_OPTIONS, software).typing](config_filename)
    # The CLI registers an atexit hook that saves the history using paths relative to the working directory.
    # atexit runs last in, first out, so registering here puts the process back in the run directory before
    # that hook fires.
    atexit.register(os.chdir, tmp_path)

    result = np.nanmin(H['f'][H['sim_ended']])
    assert np.isclose(example['result'], result), f'Best result {result} does not match registry value ' \
                                                  f'{example["result"]} for {config_filename}'
