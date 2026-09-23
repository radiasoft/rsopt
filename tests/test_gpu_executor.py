import copy
import pathlib
import pytest
from rsopt import parse
from rsopt.libe_tools.executors import create_executor_arguments
from ruamel.yaml import YAML

_CONFIG_FILE = pathlib.Path('./support/config_six_hump_camel.yaml')


@pytest.fixture
def config():
    return YAML().load(_CONFIG_FILE)


def _parse_job(config, **setup):
    _config = copy.deepcopy(config)
    _config['codes'][0]['python']['setup'].update(setup)
    return parse.parse_optimize_configuration(_config).codes[0]


def test_gpu_default_off(config):
    job = _parse_job(config, execution_type='parallel', cores=2)
    args = create_executor_arguments(job)

    assert job.setup.gpu is False
    assert args['num_procs'] == 2
    assert args['auto_assign_gpus'] is False
    assert args['match_procs_to_gpus'] is False


def test_gpu_parallel(config):
    job = _parse_job(config, execution_type='parallel', cores=2, gpu=True)
    args = create_executor_arguments(job)

    assert args['num_procs'] is None
    assert args['auto_assign_gpus'] is True
    assert args['match_procs_to_gpus'] is True


def test_gpu_serial_ignored(config):
    job = _parse_job(config, execution_type='serial', gpu=True)
    args = create_executor_arguments(job)

    assert 'auto_assign_gpus' not in args
    assert 'match_procs_to_gpus' not in args
    assert 'num_procs' not in args
