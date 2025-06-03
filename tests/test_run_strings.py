import pathlib
import pytest
import rsopt.environment
import os
import shutil
import typing
from rsopt import parse


@pytest.fixture
def setup(tmp_path,
          config: pathlib.Path,
          resource_path: pathlib.Path,
          resources: typing.List[pathlib.Path] = None):
    # copy config and needed resources in tmp_path
    shutil.copy(config, tmp_path)
    # resources should be placed in tmp_path relative to config's starting location so that they align with the
    # paths in the config file
    shutil.copytree(resource_path, tmp_path.joinpath(resource_path.relative_to(config.parent)))
    if resources:
        for ff in resources:
            shutil.copy(ff, tmp_path)


@pytest.mark.parametrize("config", (pathlib.Path("support/config_with_arguments.yml"),))
@pytest.mark.parametrize("resource_path", (pathlib.Path("./support/ignored_files"), ))
def test_app_full_paths(tmp_path, config, resource_path, setup):
    os.chdir(tmp_path)
    config_yaml = parse.read_configuration_file(config.name)
    _config = parse.parse_sample_configuration(config_yaml)

    for job in _config.codes:
        # This is the same check that libEnsemble's _check_app_exists uses
        assert os.path.isfile(rsopt.environment.get_run_command_with_path(job))
