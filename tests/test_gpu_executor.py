import copy
import pathlib
import os
import types
import pytest
from rsopt import parse
from rsopt import simulation
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


def test_gpu_serial_no_mpi_gpu_args(config):
    job = _parse_job(config, execution_type='serial', gpu=True)
    args = create_executor_arguments(job)

    assert 'auto_assign_gpus' not in args
    assert 'match_procs_to_gpus' not in args
    assert 'num_procs' not in args


class _FakeWorkerResources:
    def __init__(self, gpus):
        self.gpus = gpus

    def doihave_gpus(self):
        return bool(self.gpus)

    def set_env_to_gpus(self):
        os.environ['CUDA_VISIBLE_DEVICES'] = self.gpus


@pytest.fixture
def worker_gpus(monkeypatch):
    monkeypatch.delenv('CUDA_VISIBLE_DEVICES', raising=False)

    def _set(gpus):
        resources = types.SimpleNamespace(worker_resources=_FakeWorkerResources(gpus))
        monkeypatch.setattr(simulation.Resources, 'resources', resources)

    return _set


def test_set_worker_gpu_env_and_restore(worker_gpus):
    worker_gpus('2')
    previous = simulation.set_worker_gpu_env()

    assert os.environ['CUDA_VISIBLE_DEVICES'] == '2'
    assert previous == {'CUDA_VISIBLE_DEVICES': None}

    simulation.restore_env(previous)
    assert 'CUDA_VISIBLE_DEVICES' not in os.environ


def test_restore_prior_value(worker_gpus, monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '0,1,2,3')
    worker_gpus('3')
    previous = simulation.set_worker_gpu_env()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '3'

    simulation.restore_env(previous)
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '0,1,2,3'


def test_no_gpus_assigned(worker_gpus):
    worker_gpus('')
    assert simulation.set_worker_gpu_env() == {}
    assert 'CUDA_VISIBLE_DEVICES' not in os.environ


def test_no_resource_manager(monkeypatch):
    monkeypatch.setattr(simulation.Resources, 'resources', None)
    assert simulation.set_worker_gpu_env() == {}
