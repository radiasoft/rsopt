"""Serial Python jobs with `force_executor: True` must run through the libEnsemble Executor.

Each case runs a small mesh_scan through the full rsopt/libEnsemble stack in a temporary directory. The simulated
function records its pid, kwargs and result in the sim directory, and the objective (which always runs on the worker)
reads that result back and records its own pid, so the tests can tell whether the function ran in a separate process.
"""
import atexit
import json
import os
import pathlib
import shutil
import numpy as np
import pytest
from rsopt import parse
from rsopt import run
from rsopt import simulation
from rsopt.libe_tools import tools

COMPLETED_STATUS_MESSAGE = 'Completed'
TIMEOUT_STATUS_MESSAGE = 'Worker killed task on Timeout'

FUNCTION_SOURCE = '''
import json
import os
import os
import time


def sleepy_quadratic(x, y, t=0., label=None):
    value = x ** 2 + 10. * y
    with open('function.json', 'w') as ff:
        json.dump({'pid': os.getpid(), 'kwargs': {'x': x, 'y': y, 't': t, 'label': label}, 'value': value}, ff)
    time.sleep(t)
    return value


def objective(J):
    with open('objective_pid.txt', 'w') as ff:
        ff.write(str(os.getpid()))
    with open('function.json') as ff:
        return json.load(ff)['value']
'''

X_VALUES = [-1., 1.]
Y_VALUE = 0.5
LABEL = "it's"

pytestmark = pytest.mark.skipif(shutil.which('python') is None,
                                reason='The Executor runs Python jobs with the `python` found on PATH')


def _run(work_dir, t, timeout, force_executor=True):
    (work_dir / 'function.py').write_text(FUNCTION_SOURCE)
    config = {
        'codes': [{'python': {
            'parameters': {'x': {'min': X_VALUES[0], 'max': X_VALUES[-1], 'start': 0., 'samples': len(X_VALUES)},
                           'y': {'min': Y_VALUE, 'max': Y_VALUE, 'start': Y_VALUE}},
            'settings': {'t': t, 'label': LABEL},
            'setup': {'input_file': 'function.py', 'function': 'sleepy_quadratic', 'execution_type': 'serial',
                      'force_executor': force_executor, 'timeout': timeout},
        }}],
        'options': {'software': 'mesh_scan', 'objective_function': ['function.py', 'objective']},
    }
    _config = parse.parse_sample_configuration(config)
    H, _, _ = run.sample_modes[_config.options.software](_config).run()
    # rsopt registers an atexit hook that saves the history using paths relative to the working directory.
    # atexit runs last in, first out, so registering here puts the process back in the run directory before
    # that hook fires.
    atexit.register(os.chdir, work_dir)

    statuses = tools.parse_stat_file(work_dir / 'libE_stats.txt').status.dropna().tolist()
    sim_dirs = sorted(pathlib.Path(work_dir).glob('ensemble/worker*/sim*'))

    return H, statuses, sim_dirs


def _read_sim_dir(sim_dir):
    function_record = json.loads((sim_dir / 'function.json').read_text())
    objective_pid = int((sim_dir / 'objective_pid.txt').read_text()) \
        if (sim_dir / 'objective_pid.txt').exists() else None
    return function_record, objective_pid


def test_force_executor_completes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    H, statuses, sim_dirs = _run(tmp_path, t=0., timeout=30.)

    assert statuses == [COMPLETED_STATUS_MESSAGE] * len(X_VALUES)
    np.testing.assert_allclose(sorted(H['f']), sorted(x ** 2 + 10. * Y_VALUE for x in X_VALUES))
    assert len(sim_dirs) == len(X_VALUES)
    for sim_dir in sim_dirs:
        function_record, objective_pid = _read_sim_dir(sim_dir)
        # The objective runs on the worker; the function must have run in a process launched by the Executor
        assert function_record['pid'] != objective_pid
        assert (sim_dir / 'run_parallel_python.py').is_file()
        assert function_record['kwargs']['label'] == LABEL
        assert function_record['kwargs']['y'] == Y_VALUE


def test_force_executor_timeout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    H, statuses, sim_dirs = _run(tmp_path, t=30., timeout=1.)

    assert statuses == [TIMEOUT_STATUS_MESSAGE] * len(X_VALUES)
    np.testing.assert_array_equal(H['f'], [simulation._PENALTY] * len(X_VALUES))
    for sim_dir in sim_dirs:
        # The function started, but the objective is skipped for a timed out job
        function_record, objective_pid = _read_sim_dir(sim_dir)
        assert objective_pid is None


def test_without_force_executor_runs_on_worker(tmp_path, monkeypatch):
    # Control case: confirms the pid comparison above can tell the two execution paths apart
    monkeypatch.chdir(tmp_path)

    H, statuses, sim_dirs = _run(tmp_path, t=0., timeout=30., force_executor=False)

    assert statuses == [COMPLETED_STATUS_MESSAGE] * len(X_VALUES)
    for sim_dir in sim_dirs:
        function_record, objective_pid = _read_sim_dir(sim_dir)
        assert function_record['pid'] == objective_pid
        assert not (sim_dir / 'run_parallel_python.py').exists()
        assert function_record['kwargs']['label'] == LABEL
