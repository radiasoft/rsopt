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


# gpu_options.devices

def _parse_config(config, gpu_options=None, **setup):
    _config = copy.deepcopy(config)
    _config['codes'][0]['python']['setup'].update(setup)
    if gpu_options is not None:
        _config['options']['gpu_options'] = gpu_options
    return parse.parse_optimize_configuration(_config)


def test_gpu_options_default(config):
    assert _parse_config(config).options.gpu_options.devices is None


def test_gpu_options_devices(config):
    assert _parse_config(config, {'devices': [2, 3]}).options.gpu_options.devices == [2, 3]


@pytest.mark.parametrize('devices', [[], [2, 2], [-1], [1.5]])
def test_gpu_options_invalid_devices(config, devices):
    with pytest.raises(ValueError):
        _parse_config(config, {'devices': devices})


def test_gpu_options_unknown_field(config):
    with pytest.raises(ValueError):
        _parse_config(config, {'device': [2, 3]})


def test_gpu_options_sets_gpus_on_node(config):
    from rsopt.libe_tools.optimizer import libEnsembleOptimizer

    optimizer = libEnsembleOptimizer(_parse_config(config, {'devices': [2, 3]}))
    optimizer._configure_specs()
    optimizer._configure_sim()

    assert optimizer.libE_specs['resource_info']['gpus_on_node'] == 2
    assert optimizer.sim_specs['sim_f'].gpu_devices == [2, 3]


def test_gpu_options_default_leaves_resource_info(config):
    from rsopt.libe_tools.optimizer import libEnsembleOptimizer

    optimizer = libEnsembleOptimizer(_parse_config(config))
    optimizer._configure_specs()

    assert 'resource_info' not in optimizer.libE_specs


def _slot_resources(slots_on_node, gpus_per_slot=1, local_node_count=1, platform_info=None):
    # Attributes of libEnsemble's WorkerResources used for GPU assignment
    return types.SimpleNamespace(
        matching_slots=True,
        slots={'node': slots_on_node},
        slots_on_node=slots_on_node,
        gpus_per_rset_per_node=gpus_per_slot,
        local_node_count=local_node_count,
        platform_info=platform_info,
        doihave_gpus=lambda: True,
    )


@pytest.mark.parametrize('slots_on_node, gpus_per_slot, devices, expected', [
    ([0], 1, [2, 3], [2]),
    ([1], 1, [2, 3], [3]),
    ([1], 2, [4, 5, 6, 7], [6, 7]),
    ([0, 1], 1, [1, 3], [1, 3]),
])
def test_translate_gpu_slots(slots_on_node, gpus_per_slot, devices, expected):
    resources = _slot_resources(slots_on_node, gpus_per_slot)
    assert simulation.translate_gpu_slots(resources, devices) == expected


def test_translate_gpu_slots_out_of_range():
    with pytest.raises(ValueError, match='out of range'):
        simulation.translate_gpu_slots(_slot_resources([2]), [2, 3])


def test_translate_gpu_slots_non_matching():
    resources = _slot_resources([0])
    resources.matching_slots = False
    with pytest.raises(AssertionError):
        simulation.translate_gpu_slots(resources, [2, 3])


@pytest.fixture
def slot_resources(monkeypatch):
    for name in ('CUDA_VISIBLE_DEVICES', 'ROCR_VISIBLE_DEVICES'):
        monkeypatch.delenv(name, raising=False)

    def _set(*args, **kwargs):
        resources = _slot_resources(*args, **kwargs)
        monkeypatch.setattr(simulation.Resources, 'resources', types.SimpleNamespace(worker_resources=resources))
        return resources

    return _set


def test_set_worker_gpu_env_devices(slot_resources):
    slot_resources([1])
    previous = simulation.set_worker_gpu_env([2, 3])

    assert os.environ['CUDA_VISIBLE_DEVICES'] == '3'
    simulation.restore_env(previous)
    assert 'CUDA_VISIBLE_DEVICES' not in os.environ


@pytest.mark.parametrize('platform_info, env_name', [
    ({'gpu_setting_type': 'env', 'gpu_setting_name': 'ROCR_VISIBLE_DEVICES'}, 'ROCR_VISIBLE_DEVICES'),
    ({'gpu_setting_type': 'runner_default', 'gpu_env_fallback': 'ROCR_VISIBLE_DEVICES'}, 'ROCR_VISIBLE_DEVICES'),
    ({}, 'CUDA_VISIBLE_DEVICES'),
])
def test_set_worker_gpu_env_devices_platform_variable(slot_resources, platform_info, env_name):
    slot_resources([0], platform_info=platform_info)
    previous = simulation.set_worker_gpu_env([2, 3])

    assert os.environ[env_name] == '2'
    simulation.restore_env(previous)


def test_gpu_device_executor_arguments(config, slot_resources):
    slot_resources([1], gpus_per_slot=2, local_node_count=2)
    job = _parse_job(config, execution_type='parallel', gpu=True)
    args = simulation.gpu_device_executor_arguments(create_executor_arguments(job), [4, 5, 6, 7])

    assert args['auto_assign_gpus'] is False
    assert args['match_procs_to_gpus'] is False
    assert args['num_procs'] is None
    assert args['num_nodes'] == 2
    assert args['procs_per_node'] == 2


def test_gpu_device_executor_arguments_no_gpus(config, monkeypatch):
    monkeypatch.setattr(simulation.Resources, 'resources', None)
    job = _parse_job(config, execution_type='parallel', gpu=True)
    args = create_executor_arguments(job)

    assert simulation.gpu_device_executor_arguments(args, [2, 3]) is args
