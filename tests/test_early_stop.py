"""Unit tests for early stopping: the monitor, its configuration, and the Executor polling loop."""
import copy
import os
import pathlib
import time
import types
import pytest
from libensemble import message_numbers
from rsopt import parse
# rsopt.simulation must be imported after rsopt.parse (circular import through rsopt.codes)
from rsopt import simulation
from rsopt import early_stop
from rsopt.configuration.schemas.setup import EarlyStopSetup
from rsopt.early_stop import EarlyStop, EarlyStopError, EarlyStopMonitor

FUNCTIONS = '''
import os
import time
from rsopt.early_stop import EarlyStop


def continue_member(J):
    return EarlyStop.CONTINUE


def stop_success_member(J):
    return EarlyStop.STOP_SUCCESS


def stop_fail_member(J):
    return EarlyStop.STOP_FAIL


def continue_string(J):
    return 'continue'


def stop_success_string(J):
    return 'stop_success'


def stop_fail_string(J):
    return 'stop_fail'


def returns_none(J):
    return None


def returns_true(J):
    return True


def returns_stop(J):
    return 'stop'


def raises(J):
    raise RuntimeError('broken early stop function')


def mutates(J):
    J['inputs']['x'] = 'changed'
    return 'continue'


def hangs(J):
    time.sleep(600)


def record(J):
    with open('record.txt', 'w') as ff:
        ff.write(repr(J['inputs']))
    return 'continue'
'''


@pytest.fixture
def functions_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / 'early_stop_functions.py'
    path.write_text(FUNCTIONS)
    return path


class FakeClock:
    def __init__(self):
        self.now = 0.

    def __call__(self):
        return self.now


def _monitor(functions_file, function_name, interval=10., on_error='raise', clock=None):
    setup = EarlyStopSetup(function=[str(functions_file), function_name], interval=interval, on_error=on_error)
    return EarlyStopMonitor(setup, clock=clock or FakeClock())


def _run_check(monitor, J=None, timeout=30.):
    """Start a check (the clock must already be past the interval) and wait for its decision."""
    J = J if J is not None else {'inputs': {'x': 1.}}
    assert monitor.update(J) is EarlyStop.CONTINUE
    assert monitor._runner.running
    end = time.monotonic() + timeout
    while monitor._runner.running:
        assert time.monotonic() < end, 'early stop check did not finish'
        decision = monitor.update(J)
        time.sleep(0.02)
    return decision


# Monitor: interval logic, with a stub runner

class StubRunner:
    def __init__(self):
        self.calls = []
        self.running = False
        self.result = None
        self.terminated = 0

    def start(self, J):
        assert not self.running
        self.calls.append(J)
        self.running = True

    def poll(self):
        if self.result is None:
            return None
        result, self.result = self.result, None
        self.running = False
        return result

    def finish(self, value):
        self.result = early_stop.user_function.Result(value=value)

    def terminate(self):
        self.terminated += 1


@pytest.fixture
def stubbed(functions_file):
    clock = FakeClock()
    monitor = _monitor(functions_file, 'continue_string', interval=10., clock=clock)
    runner = StubRunner()
    monitor._runner = runner
    return monitor, runner, clock


def test_no_check_before_interval(stubbed):
    monitor, runner, clock = stubbed
    clock.now = 9.9
    assert monitor.update({}) is EarlyStop.CONTINUE
    assert runner.calls == []


def test_first_check_at_interval_and_one_in_flight(stubbed):
    monitor, runner, clock = stubbed
    clock.now = 10.
    J = {'inputs': {'x': 1.}}
    assert monitor.update(J) is EarlyStop.CONTINUE
    assert runner.calls == [J]

    # Still running: no new check is started however much time passes
    clock.now = 100.
    assert monitor.update(J) is EarlyStop.CONTINUE
    assert runner.calls == [J]


def test_next_check_is_interval_after_previous_finished(stubbed):
    monitor, runner, clock = stubbed
    clock.now = 10.
    monitor.update({})
    clock.now = 25.
    runner.finish('continue')
    assert monitor.update({}) is EarlyStop.CONTINUE
    assert not runner.running

    clock.now = 34.9
    monitor.update({})
    assert not runner.running
    clock.now = 35.
    monitor.update({})
    assert runner.running


def test_finished_check_returns_its_decision(stubbed):
    monitor, runner, clock = stubbed
    clock.now = 10.
    monitor.update({})
    runner.finish('stop_success')
    assert monitor.update({}) is EarlyStop.STOP_SUCCESS


def test_terminate_stops_runner(stubbed):
    monitor, runner, clock = stubbed
    monitor.terminate()
    assert runner.terminated == 1


# Monitor: decisions, with the real runner

@pytest.mark.parametrize('function_name, expected', [
    ('continue_member', EarlyStop.CONTINUE),
    ('stop_success_member', EarlyStop.STOP_SUCCESS),
    ('stop_fail_member', EarlyStop.STOP_FAIL),
    ('continue_string', EarlyStop.CONTINUE),
    ('stop_success_string', EarlyStop.STOP_SUCCESS),
    ('stop_fail_string', EarlyStop.STOP_FAIL),
])
def test_valid_results(functions_file, function_name, expected):
    clock = FakeClock()
    monitor = _monitor(functions_file, function_name, clock=clock)
    clock.now = 10.
    assert _run_check(monitor) is expected


@pytest.mark.parametrize('function_name, expected_repr', [
    ('returns_none', 'None'),
    ('returns_true', 'True'),
    ('returns_stop', "'stop'"),
])
def test_invalid_result_raises(functions_file, function_name, expected_repr):
    clock = FakeClock()
    monitor = _monitor(functions_file, function_name, clock=clock)
    clock.now = 10.
    with pytest.raises(EarlyStopError, match=f'returned {expected_repr}') as e:
        _run_check(monitor)
    assert function_name in str(e.value)
    assert not pathlib.Path(early_stop.ERROR_FILE_NAME).exists()


def test_exception_raises_with_traceback(functions_file):
    clock = FakeClock()
    monitor = _monitor(functions_file, 'raises', clock=clock)
    clock.now = 10.
    with pytest.raises(EarlyStopError) as e:
        _run_check(monitor)
    assert 'Traceback' in str(e.value)
    assert 'RuntimeError: broken early stop function' in str(e.value)


@pytest.mark.parametrize('function_name, expected_text', [
    ('returns_none', 'returned None'),
    ('returns_stop', "returned 'stop'"),
    ('raises', 'RuntimeError: broken early stop function'),
])
def test_on_error_fail(functions_file, function_name, expected_text):
    clock = FakeClock()
    monitor = _monitor(functions_file, function_name, on_error='fail', clock=clock)
    clock.now = 10.
    assert _run_check(monitor) is EarlyStop.STOP_FAIL
    assert expected_text in pathlib.Path(early_stop.ERROR_FILE_NAME).read_text()


def test_function_receives_a_copy_of_J(functions_file):
    clock = FakeClock()
    J = {'inputs': {'x': 1.}}
    monitor = _monitor(functions_file, 'mutates', clock=clock)
    clock.now = 10.
    assert _run_check(monitor, J) is EarlyStop.CONTINUE
    assert J == {'inputs': {'x': 1.}}


def test_function_runs_in_current_directory(functions_file, tmp_path, monkeypatch):
    sim_dir = tmp_path / 'sim'
    sim_dir.mkdir()
    monkeypatch.chdir(sim_dir)
    clock = FakeClock()
    monitor = _monitor(functions_file, 'record', clock=clock)
    clock.now = 10.
    _run_check(monitor, {'inputs': {'x': 2.5}})
    assert (sim_dir / 'record.txt').read_text() == "{'x': 2.5}"


def test_terminate_kills_check_in_flight(functions_file):
    clock = FakeClock()
    monitor = _monitor(functions_file, 'hangs', clock=clock)
    clock.now = 10.
    monitor.update({})
    pid = monitor._runner._call.process.pid

    monitor.terminate()
    assert not monitor._runner.running
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    # Terminating again, or with nothing running, is harmless
    monitor.terminate()


# Configuration

CONFIG = {
    'codes': [{'python': {
        'parameters': {'x': {'min': -1., 'max': 1., 'start': 0., 'samples': 2}},
        'setup': {'input_file': 'function.py', 'function': 'f', 'execution_type': 'serial', 'force_executor': True},
    }}],
    'options': {'software': 'mesh_scan', 'objective_function': ['function.py', 'objective']},
}


@pytest.fixture
def config(functions_file):
    (functions_file.parent / 'function.py').write_text('def f(x):\n    return x\n\n\ndef objective(J):\n    return 0.\n')
    return copy.deepcopy(CONFIG)


def _parse(config, early_stop_options, **setup):
    config['codes'][0]['python']['setup'].update(setup)
    if early_stop_options is not None:
        config['codes'][0]['python']['setup']['early_stop'] = early_stop_options
    return parse.parse_sample_configuration(config).codes[0]


def test_config_defaults(config, functions_file):
    job = _parse(config, {'function': [functions_file.name, 'continue_string']})
    assert job.setup.early_stop.interval == 30.
    assert job.setup.early_stop.on_error is early_stop.EarlyStopOnError.RAISE
    assert job.setup.early_stop.function == [str(functions_file), 'continue_string']


def test_config_not_set(config):
    assert _parse(config, None).setup.early_stop is None


def test_config_options(config, functions_file):
    job = _parse(config, {'function': [functions_file.name, 'continue_string'], 'interval': 2.5, 'on_error': 'fail'})
    assert job.setup.early_stop.interval == 2.5
    assert job.setup.early_stop.on_error is early_stop.EarlyStopOnError.FAIL


def test_config_path_resolved_to_absolute(config, functions_file, tmp_path):
    (tmp_path / 'sub').mkdir()
    job = _parse(config, {'function': ['sub/../early_stop_functions.py', 'continue_string']})
    assert job.setup.early_stop.function[0] == str(functions_file)
    assert pathlib.Path(job.setup.early_stop.function[0]).is_absolute()


@pytest.mark.parametrize('early_stop_options', [
    {'function': ['early_stop_functions.py', 'continue_string'], 'unknown': 1},
    {'function': ['early_stop_functions.py', 'continue_string'], 'on_error': 'continue'},
    {'function': ['early_stop_functions.py', 'continue_string'], 'interval': 0},
    {'function': ['early_stop_functions.py']},
    {'interval': 1.},
    {'function': ['missing.py', 'continue_string']},
    {'function': ['early_stop_functions.py', 'missing_function']},
])
def test_config_invalid(config, early_stop_options):
    with pytest.raises(ValueError):
        _parse(config, early_stop_options)


def test_config_rejected_without_executor(config, functions_file):
    with pytest.raises(ValueError, match='force_executor'):
        _parse(config, {'function': [functions_file.name, 'continue_string']}, force_executor=False)


# Executor polling loop

class FakeTask:
    def __init__(self, finish_after=None, state='FINISHED'):
        self.polls = 0
        self.finish_after = finish_after
        self.final_state = state
        self.state = 'RUNNING'
        self.finished = False
        self.runtime = 0.
        self.killed = False

    def poll(self):
        self.polls += 1
        if self.finish_after is not None and self.polls >= self.finish_after:
            self.finished = True
            self.state = self.final_state

    def kill(self):
        self.killed = True
        self.finished = True
        self.state = 'USER_KILLED'


class FakeExecutor:
    def __init__(self, task, signals=()):
        self.task = task
        self.signals = list(signals)
        self.manager_signal = None

    def submit(self, **kwargs):
        return self.task

    def manager_poll(self):
        self.manager_signal = self.signals.pop(0) if self.signals else None
        return self.manager_signal


class FakeMonitor:
    """Replays a list of decisions (or exceptions) and records calls."""
    instances = []

    def __init__(self, early_stop_setup):
        self.decisions = list(early_stop_setup.decisions)
        self.updates = 0
        self.terminated = False
        FakeMonitor.instances.append(self)

    def update(self, J):
        self.updates += 1
        decision = self.decisions.pop(0) if self.decisions else EarlyStop.CONTINUE
        if isinstance(decision, Exception):
            raise decision
        return decision

    def terminate(self):
        self.terminated = True


@pytest.fixture
def loop(monkeypatch):
    monkeypatch.setattr(simulation, '_POLL_TIME', 0)
    monkeypatch.setattr(early_stop, 'EarlyStopMonitor', FakeMonitor)
    FakeMonitor.instances = []

    def _run(task, signals=(), decisions=None, timeout=1e9):
        executor = FakeExecutor(task, signals)
        monkeypatch.setattr(simulation.Executor, 'executor', executor)
        early_stop_setup = types.SimpleNamespace(decisions=decisions) if decisions is not None else None
        job = types.SimpleNamespace(
            _executor_arguments={}, use_mpi=False,
            setup=types.SimpleNamespace(gpu=False, timeout=timeout, early_stop=early_stop_setup),
        )
        sim = simulation.SimulationFunction(jobs=[job], objective_function=None)
        sim.libE_info = {'H_rows': [7]}
        halt = sim._run_executor_job(job, None)
        monitor = FakeMonitor.instances[0] if FakeMonitor.instances else None
        return halt, sim.J['sim_status'], monitor

    return _run


def test_loop_without_early_stop(loop):
    task = FakeTask(finish_after=3)
    halt, status, monitor = loop(task)
    assert (halt, status, monitor) == (False, message_numbers.WORKER_DONE, None)
    assert not task.killed


@pytest.mark.parametrize('signal', [message_numbers.MAN_SIGNAL_FINISH, message_numbers.MAN_SIGNAL_KILL])
def test_loop_manager_signal(loop, signal):
    task = FakeTask()
    halt, status, _ = loop(task, signals=[None, None, signal])
    assert halt
    assert status == signal
    assert task.killed
    assert task.polls == 3


def test_loop_early_stop_success(loop):
    task = FakeTask()
    halt, status, monitor = loop(task, decisions=[EarlyStop.CONTINUE, EarlyStop.STOP_SUCCESS])
    assert not halt
    assert status == message_numbers.WORKER_DONE
    assert task.killed
    assert monitor.terminated


def test_loop_early_stop_fail(loop):
    task = FakeTask()
    halt, status, monitor = loop(task, decisions=[EarlyStop.STOP_FAIL])
    assert halt
    assert status == message_numbers.TASK_FAILED
    assert task.killed
    assert monitor.terminated


def test_loop_early_stop_error_kills_task_and_raises(loop):
    task = FakeTask()
    with pytest.raises(EarlyStopError):
        loop(task, decisions=[EarlyStop.CONTINUE, EarlyStopError('broken')])
    assert task.killed
    assert FakeMonitor.instances[0].terminated


def test_loop_finished_task_wins_over_early_stop(loop):
    task = FakeTask(finish_after=1)
    halt, status, monitor = loop(task, decisions=[EarlyStop.STOP_FAIL])
    assert (halt, status) == (False, message_numbers.WORKER_DONE)
    assert monitor.updates == 0
    assert not task.killed
    assert monitor.terminated


def test_loop_manager_signal_wins_over_early_stop(loop):
    task = FakeTask()
    halt, status, monitor = loop(task, signals=[message_numbers.MAN_SIGNAL_FINISH], decisions=[EarlyStop.STOP_SUCCESS])
    assert (halt, status) == (True, message_numbers.MAN_SIGNAL_FINISH)
    assert monitor.updates == 0


def test_loop_timeout_wins_over_early_stop(loop):
    task = FakeTask()
    task.runtime = 10.
    halt, status, monitor = loop(task, decisions=[EarlyStop.STOP_SUCCESS], timeout=5.)
    assert (halt, status) == (True, message_numbers.WORKER_KILL_ON_TIMEOUT)
    assert monitor.updates == 0
