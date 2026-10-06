"""Early stopping through the full rsopt/libEnsemble stack.

Each case runs a small mesh_scan of a Python job with `force_executor: True` in a temporary directory. The simulated
function writes a heartbeat file while it sleeps, so the tests can tell whether it was stopped. The early stop
functions run in the sim directory alongside it.
"""
import atexit
import os
import pathlib
import shutil
import time
import numpy as np
import pytest
from libensemble.manager import LoggedException
from rsopt import parse
from rsopt import run
from rsopt import simulation
from rsopt.early_stop import ERROR_FILE_NAME
from rsopt.libe_tools import tools

COMPLETED_STATUS_MESSAGE = 'Completed'
TASK_FAILED_STATUS_MESSAGE = 'Task Failed during run'
TIMEOUT_STATUS_MESSAGE = 'Worker killed task on Timeout'

FUNCTION_SOURCE = '''
import time


def sleepy_quadratic(x, y, t=0.):
    end = time.time() + t
    while True:
        with open('heartbeat.txt', 'w') as ff:
            ff.write(str(time.time()))
        if time.time() >= end:
            break
        time.sleep(0.1)
    return x ** 2 + 10. * y


def objective(J):
    return J['inputs']['x'] ** 2 + 10. * J['inputs']['y']
'''

EARLY_STOP_SOURCE = '''
import os
import time
from rsopt.early_stop import EarlyStop


def stop_success(J):
    return EarlyStop.STOP_SUCCESS


def stop_fail(J):
    return 'stop_fail'


def raises(J):
    raise RuntimeError('broken early stop function')


def hangs(J):
    time.sleep(600)


def record_and_continue(J):
    with open('early_stop_record.txt', 'a') as ff:
        ff.write(f"{os.path.exists('heartbeat.txt')} {J['inputs']['x']}\\n")
    return 'continue'
'''

X_VALUES = [-1., 1.]
Y_VALUE = 0.5

pytestmark = pytest.mark.skipif(shutil.which('python') is None,
                                reason='The Executor runs Python jobs with the `python` found on PATH')


def _config(t, timeout, early_stop, x_values=X_VALUES):
    setup = {'input_file': 'function.py', 'function': 'sleepy_quadratic', 'execution_type': 'serial',
             'force_executor': True, 'timeout': timeout}
    if early_stop is not None:
        setup['early_stop'] = early_stop
    return {
        'codes': [{'python': {
            'parameters': {'x': {'min': x_values[0], 'max': x_values[-1], 'start': 0., 'samples': len(x_values)},
                           'y': {'min': Y_VALUE, 'max': Y_VALUE, 'start': Y_VALUE}},
            'settings': {'t': t},
            'setup': setup,
        }}],
        'options': {'software': 'mesh_scan', 'objective_function': ['function.py', 'objective']},
    }


def _run(work_dir, t, timeout=60., early_stop=None, **kwargs):
    (work_dir / 'function.py').write_text(FUNCTION_SOURCE)
    (work_dir / 'early_stop.py').write_text(EARLY_STOP_SOURCE)
    _config_model = parse.parse_sample_configuration(_config(t, timeout, early_stop, **kwargs))
    # rsopt registers an atexit hook that saves the history using paths relative to the working directory.
    # atexit runs last in, first out, so registering here puts the process back in the run directory before
    # that hook fires. Registered before the run so it is in place even if the run raises.
    atexit.register(os.chdir, work_dir)
    H, _, _ = run.sample_modes[_config_model.options.software](_config_model).run()

    return H, _stats(work_dir), _sim_dirs(work_dir)


def _stats(work_dir):
    stats = tools.parse_stat_file(work_dir / 'libE_stats.txt').dropna(subset=['status'])
    return stats.status.tolist(), stats.time.astype(float).tolist()


def _sim_dirs(work_dir):
    return sorted(pathlib.Path(work_dir).glob('ensemble/worker*/sim*'))


def _expected_f():
    return sorted(x ** 2 + 10. * Y_VALUE for x in X_VALUES)


def test_continue_runs_to_completion(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    H, (statuses, _), sim_dirs = _run(tmp_path, t=4., early_stop={'function': ['early_stop.py', 'record_and_continue'],
                                                                  'interval': 1.})

    assert statuses == [COMPLETED_STATUS_MESSAGE] * len(X_VALUES)
    np.testing.assert_allclose(sorted(H['f']), _expected_f())
    for sim_dir in sim_dirs:
        # Checks ran repeatedly, in the sim directory, with this sim's inputs
        records = (sim_dir / 'early_stop_record.txt').read_text().splitlines()
        assert len(records) >= 2
        assert len(set(records)) == 1
        exists, x = records[0].split()
        assert exists == 'True'
        assert float(x) in X_VALUES


def test_stop_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    H, (statuses, times), sim_dirs = _run(tmp_path, t=60., early_stop={'function': ['early_stop.py', 'stop_success'],
                                                                       'interval': 1.})

    assert statuses == [COMPLETED_STATUS_MESSAGE] * len(X_VALUES)
    assert max(times) < 30.
    # The job is treated as finished: the objective is evaluated
    np.testing.assert_allclose(sorted(H['f']), _expected_f())
    for sim_dir in sim_dirs:
        assert (sim_dir / 'heartbeat.txt').exists()


def test_stop_fail(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    H, (statuses, times), _ = _run(tmp_path, t=60., early_stop={'function': ['early_stop.py', 'stop_fail'],
                                                                'interval': 1.})

    assert statuses == [TASK_FAILED_STATUS_MESSAGE] * len(X_VALUES)
    assert max(times) < 30.
    np.testing.assert_array_equal(H['f'], [simulation._PENALTY] * len(X_VALUES))


def test_error_with_on_error_fail(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    H, (statuses, _), sim_dirs = _run(tmp_path, t=60., early_stop={'function': ['early_stop.py', 'raises'],
                                                                   'interval': 1., 'on_error': 'fail'})

    assert statuses == [TASK_FAILED_STATUS_MESSAGE] * len(X_VALUES)
    np.testing.assert_array_equal(H['f'], [simulation._PENALTY] * len(X_VALUES))
    for sim_dir in sim_dirs:
        assert 'RuntimeError: broken early stop function' in (sim_dir / ERROR_FILE_NAME).read_text()


def test_error_with_on_error_raise(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # libEnsemble re-raises the worker's exception in the manager, with the early stop function's traceback
    with pytest.raises(LoggedException, match='EarlyStopError') as e:
        _run(tmp_path, t=60., early_stop={'function': ['early_stop.py', 'raises'], 'interval': 1.},
             x_values=[0.])
    assert 'RuntimeError: broken early stop function' in str(e.value)

    # The simulation was killed, not left running after the ensemble stopped
    sim_dirs = _sim_dirs(tmp_path)
    assert len(sim_dirs) == 1
    heartbeat = sim_dirs[0] / 'heartbeat.txt'
    last_beat = heartbeat.read_text()
    time.sleep(1.)
    assert heartbeat.read_text() == last_beat


def test_hung_early_stop_does_not_block_timeout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    H, (statuses, times), _ = _run(tmp_path, t=60., timeout=4.,
                                   early_stop={'function': ['early_stop.py', 'hangs'], 'interval': 1.})

    assert statuses == [TIMEOUT_STATUS_MESSAGE] * len(X_VALUES)
    assert max(times) < 30.
    np.testing.assert_array_equal(H['f'], [simulation._PENALTY] * len(X_VALUES))
