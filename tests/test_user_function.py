import multiprocessing
import os
import time
import pytest
from rsopt.libe_tools import user_function

_ENV_NAME = 'RSOPT_TEST_USER_FUNCTION_ENV'

FUNCTIONS = f'''
import os
import time


def add(a, b=0):
    return a + b


def raises():
    raise ValueError('bad value from user function')


def unpicklable():
    return lambda: None


def exits():
    os._exit(3)


def hangs():
    time.sleep(600)


def large():
    return b'x' * 10_000_000


def environment_and_cwd():
    return os.environ.get('{_ENV_NAME}'), os.getcwd()
'''


@pytest.fixture(params=['spawn', 'forkserver', 'fork'])
def start_method(request, monkeypatch):
    monkeypatch.setattr(user_function, '_mp_context', multiprocessing.get_context(request.param))
    return request.param


@pytest.fixture
def functions_file(tmp_path):
    path = tmp_path / 'functions.py'
    path.write_text(FUNCTIONS)
    return path


def _wait(runner, timeout=30.):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        result = runner.poll()
        if result is not None:
            return result
        time.sleep(0.02)
    runner.terminate()
    raise TimeoutError('User function did not finish')


def test_returns_value(start_method, functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'add')
    runner.start(2, b=3)
    assert runner.running

    result = _wait(runner)
    assert not result.failed
    assert result.value == 5
    assert not runner.running


def test_runner_can_be_reused(start_method, functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'add')
    for i in range(2):
        runner.start(i, b=1)
        assert _wait(runner).value == i + 1


def test_exception_reports_traceback(start_method, functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'raises')
    runner.start()

    result = _wait(runner)
    assert result.failed
    assert result.value is None
    assert 'Traceback' in result.error
    assert 'ValueError: bad value from user function' in result.error


def test_missing_function_reports_error(start_method, functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'does_not_exist')
    runner.start()

    result = _wait(runner)
    assert result.failed
    assert 'does_not_exist' in result.error


def test_unpicklable_return_value_is_an_error(start_method, functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'unpicklable')
    runner.start()

    result = _wait(runner)
    assert result.failed
    assert 'pickle' in result.error.lower()


def test_child_exit_without_result(start_method, functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'exits')
    runner.start()

    result = _wait(runner)
    assert result.failed
    assert 'exited with code 3' in result.error
    assert not runner.running


def test_large_result_does_not_deadlock(start_method, functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'large')
    runner.start()

    assert len(_wait(runner).value) == 10_000_000


def test_hung_function_does_not_block_and_can_be_terminated(start_method, functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'hangs')
    runner.start()
    pid = runner._call.process.pid

    start = time.monotonic()
    for _ in range(5):
        assert runner.poll() is None
    assert time.monotonic() - start < 1.

    start = time.monotonic()
    runner.terminate()
    assert time.monotonic() - start < user_function._JOIN_TIMEOUT
    assert not runner.running
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_terminate_and_poll_are_safe_when_idle(functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'add')
    runner.terminate()
    assert runner.poll() is None

    runner.start(1)
    _wait(runner)
    runner.terminate()
    runner.terminate()
    assert runner.poll() is None


def test_only_one_call_in_flight(functions_file):
    runner = user_function.UserFunctionProcess(functions_file, 'hangs')
    runner.start()
    try:
        with pytest.raises(RuntimeError):
            runner.start()
    finally:
        runner.terminate()


def test_child_sees_current_environment_and_cwd(start_method, functions_file, tmp_path, monkeypatch):
    run_dir = tmp_path / 'run'
    run_dir.mkdir()
    monkeypatch.chdir(run_dir)
    runner = user_function.UserFunctionProcess(functions_file, 'environment_and_cwd')

    monkeypatch.setenv(_ENV_NAME, 'first')
    runner.start()
    assert _wait(runner).value == ('first', str(run_dir))

    monkeypatch.setenv(_ENV_NAME, 'second')
    runner.start()
    assert _wait(runner).value == ('second', str(run_dir))

    monkeypatch.delenv(_ENV_NAME)
    runner.start()
    assert _wait(runner).value == (None, str(run_dir))
