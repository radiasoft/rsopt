import multiprocessing
import os
import pytest
from rsopt.libe_tools import serial_python

_ENV_NAME = 'RSOPT_TEST_SERIAL_PYTHON_ENV'


def _read_env():
    return os.environ.get(_ENV_NAME)


@pytest.mark.parametrize('start_method', ['fork', 'spawn', 'forkserver'])
def test_run_process_sees_current_environment(monkeypatch, start_method):
    # Under 'forkserver' children inherit the environment from when the fork server started, not the parent's current
    # environment. Values set between calls (e.g. CUDA_VISIBLE_DEVICES for each trial) must still reach the function.
    monkeypatch.setattr(serial_python, '_mp_context', multiprocessing.get_context(start_method))

    monkeypatch.setenv(_ENV_NAME, 'first')
    assert serial_python.run_process(_read_env)[serial_python.RESULT] == 'first'

    monkeypatch.setenv(_ENV_NAME, 'second')
    assert serial_python.run_process(_read_env)[serial_python.RESULT] == 'second'

    monkeypatch.delenv(_ENV_NAME)
    assert serial_python.run_process(_read_env)[serial_python.RESULT] is None
