import json
import pathlib
import subprocess
import sys
import numpy as np
import pytest
from rsopt import parse
from rsopt import util
from rsopt.codes import python

# TODO: Need tests for:
# opal
# elegant
# genesis
# user

INPUTS = {'a': 1, 'b': 2.5, 'c': 'c'}

# Writes the kwargs it was called with so a test can check what the generated run file passed in
_FUNCTION_SOURCE = '''
import json


def foo(**kwargs):
    with open('called_with.json', 'w') as ff:
        json.dump(kwargs, ff)
    return 0
'''

EXECUTOR_SETUPS = {
    'parallel': {'execution_type': 'parallel', 'cores': 2},
    'rsmpi': {'execution_type': 'rsmpi', 'cores': 2},
    'force_executor': {'execution_type': 'serial', 'force_executor': True},
}


@pytest.fixture
def input_file(tmp_path):
    path = tmp_path / 'test.py'
    path.write_text(_FUNCTION_SOURCE)
    return path


@pytest.fixture
def run_dir(tmp_path):
    path = tmp_path / 'run'
    path.mkdir()
    return path


def _job(input_file, **setup):
    config = {
        'codes': [{'python': {'setup': {'input_file': str(input_file), 'function': 'foo',
                                        'execution_type': 'serial', **setup}}}],
        'options': {'software': 'mesh_scan'},
    }
    return parse.parse_sample_configuration(config).codes[0]


def _run_file(run_dir):
    return pathlib.Path(run_dir) / python._PARALLEL_PYTHON_RUN_FILE


def test_serial_python(input_file, run_dir):
    job = _job(input_file)

    job.generate_input_file(dict(INPUTS), run_dir, is_parallel=False)

    assert not job.use_executor
    assert not _run_file(run_dir).exists()


@pytest.mark.parametrize('setup', EXECUTOR_SETUPS.values(), ids=EXECUTOR_SETUPS.keys())
def test_executor_python(input_file, run_dir, setup):
    job = _job(input_file, **setup)

    job.generate_input_file(dict(INPUTS), run_dir, is_parallel=job.use_mpi)

    assert job.use_executor
    assert job.run_file_name == python._PARALLEL_PYTHON_RUN_FILE
    assert _run_file(run_dir).is_file()


def test_argument_dict(input_file, run_dir):
    job = _job(input_file, **EXECUTOR_SETUPS['parallel'])

    job.generate_input_file(dict(INPUTS), run_dir, is_parallel=True)
    input_dict = util.run_path_as_module(_run_file(run_dir)).input_dict

    assert input_dict == INPUTS


def test_numeric_only_argument_dict(input_file, run_dir):
    inputs = {'a': 1, 'b': 2.5, 'v': [1., 2.]}
    job = _job(input_file, **EXECUTOR_SETUPS['parallel'])

    job.generate_input_file(dict(inputs), run_dir, is_parallel=True)

    assert util.run_path_as_module(_run_file(run_dir)).input_dict == inputs


def test_run_file_calls_function(input_file, run_dir):
    job = _job(input_file, **EXECUTOR_SETUPS['parallel'])
    job.generate_input_file(dict(INPUTS), run_dir, is_parallel=True)

    subprocess.run([sys.executable, python._PARALLEL_PYTHON_RUN_FILE], cwd=run_dir, check=True)

    assert json.loads((run_dir / 'called_with.json').read_text()) == INPUTS


def test_run_file_from_module(run_dir):
    # Any importable module works; the run file imports it instead of loading a file by path
    config = {
        'codes': [{'python': {'setup': {'module': 'json', 'function': 'dumps',
                                        **EXECUTOR_SETUPS['parallel']}}}],
        'options': {'software': 'mesh_scan'},
    }
    job = parse.parse_sample_configuration(config).codes[0]

    job.generate_input_file({'obj': 1}, run_dir, is_parallel=True)
    module = util.run_path_as_module(_run_file(run_dir))

    assert module.m.__name__ == 'json'
    assert module.input_dict == {'obj': 1}


@pytest.mark.parametrize('inputs, expected', [
    ({'s': "it's"}, {'s': "it's"}),
    ({'s': 'say "hi"'}, {'s': 'say "hi"'}),
    ({'s': 'C:\\new\\path'}, {'s': 'C:\\new\\path'}),
    ({'s': ''}, {'s': ''}),
    ({'flag': True, 'none': None}, {'flag': True, 'none': None}),
    ({'nested': {'a': [1, 'b']}, 't': (1, 2)}, {'nested': {'a': [1, 'b']}, 't': (1, 2)}),
    ({'f': np.float64(1.5), 'i': np.int64(3), 'v': np.array([1., 2.])}, {'f': 1.5, 'i': 3, 'v': [1., 2.]}),
], ids=['single_quote', 'double_quote', 'backslash', 'empty_str', 'bool_none', 'containers', 'numpy'])
def test_argument_values_round_trip(input_file, run_dir, inputs, expected):
    job = _job(input_file, **EXECUTOR_SETUPS['parallel'])

    job.generate_input_file(dict(inputs), run_dir, is_parallel=True)

    assert util.run_path_as_module(_run_file(run_dir)).input_dict == expected


def test_inputs_not_modified(input_file, run_dir):
    job = _job(input_file, **EXECUTOR_SETUPS['parallel'])
    inputs = dict(INPUTS)

    job.generate_input_file(inputs, run_dir, is_parallel=True)

    assert inputs == INPUTS
