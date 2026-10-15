"""Live copy of the libEnsemble logs into run_dir (rsopt.libe_tools.log_tee).

`test_tee_main_path` is the canary for libEnsemble upgrades: it fails if libEnsemble's logging setup no longer looks
the way log_tee expects.

libEnsemble keeps process-global logging state, so these tests must not assume a fresh logging state.

Run from inside `tests/`.
"""
import importlib
import logging
import warnings
import pytest
from libensemble.comms.logs import LogConfig
from rsopt import run
from rsopt import run_archive
from rsopt.libe_tools import log_tee
import archive_helpers as helpers

LOCAL_LOGS = ('ensemble.log', 'libE_stats.txt')
MARKER = 'PRE-EXISTING MARKER LINE FROM AN EARLIER RUN\n'


def _libE_module():
    return importlib.import_module('libensemble.libE')


ORIGINAL_HOOK = _libE_module().manager_logging_config


def _local_sizes(work_dir):
    return {name: (work_dir / name).stat().st_size if (work_dir / name).exists() else 0 for name in LOCAL_LOGS}


def _this_run(work_dir, sizes, name):
    return (work_dir / name).read_bytes()[sizes[name]:]


def _seed_local_logs(work_dir):
    for name in LOCAL_LOGS:
        (work_dir / name).write_text(MARKER)


def _tee_handlers():
    names = (LogConfig.config.name, LogConfig.config.stats_name)
    return [h for name in names for h in logging.getLogger(name).handlers if isinstance(h, log_tee.TeeFileHandler)]


def test_tee_main_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config, _ = helpers.start(tmp_path)
    sizes = _local_sizes(tmp_path)

    with warnings.catch_warnings():
        warnings.simplefilter('error', run_archive.RsoptArchiveWarning)
        helpers.runner(config).run()

    run_dir = helpers.run_dir(tmp_path)
    for name in LOCAL_LOGS:
        assert (run_dir / name).read_bytes() == _this_run(tmp_path, sizes, name)
    stats = (run_dir / 'libE_stats.txt').read_text()
    assert 'Starting ensemble at' in stats
    assert 'Exiting ensemble at' in stats
    assert 'sim_id' in stats


def test_append_split(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_local_logs(tmp_path)
    config, _ = helpers.start(tmp_path)

    helpers.runner(config).run()

    run_dir = helpers.run_dir(tmp_path)
    for name in LOCAL_LOGS:
        local = (tmp_path / name).read_text()
        assert local.startswith(MARKER)
        assert len(local) > len(MARKER)
        copy = (run_dir / name).read_text()
        assert MARKER not in copy
        assert local == MARKER + copy


@pytest.mark.parametrize('objective', ['objective', 'raises'])
def test_patch_restored(tmp_path, monkeypatch, objective):
    monkeypatch.chdir(tmp_path)
    config, _ = helpers.start(tmp_path, objective=objective)

    try:
        helpers.runner(config).run()
    except Exception:
        assert objective == 'raises'
    else:
        assert objective == 'objective'

    assert _libE_module().manager_logging_config is ORIGINAL_HOOK
    assert _tee_handlers() == []
    # The run_dir copies were written up to the end, including after the failure
    assert 'Exiting ensemble at' in (helpers.run_dir(tmp_path) / 'libE_stats.txt').read_text()


def test_fallback_when_handler_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_local_logs(tmp_path)
    config, _ = helpers.start(tmp_path)
    sizes = _local_sizes(tmp_path)
    monkeypatch.setattr(log_tee, '_find_file_handler', lambda logger, local_path: None)

    with pytest.warns(run_archive.RsoptArchiveWarning, match='Could not find the libEnsemble handler'):
        H, _, _ = helpers.runner(config).run()

    assert len(H) == len(helpers.X_VALUES)
    run_dir = helpers.run_dir(tmp_path)
    for name in LOCAL_LOGS:
        assert (run_dir / name).read_bytes() == _this_run(tmp_path, sizes, name)
    assert 'Exiting ensemble at' in (run_dir / 'libE_stats.txt').read_text()


def test_fallback_when_hook_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config, _ = helpers.start(tmp_path)
    sizes = _local_sizes(tmp_path)
    monkeypatch.setattr(log_tee, '_locate_hook', lambda: None)

    with pytest.warns(run_archive.RsoptArchiveWarning, match='Could not attach to libEnsemble logging'):
        helpers.runner(config).run()

    run_dir = helpers.run_dir(tmp_path)
    for name in LOCAL_LOGS:
        assert (run_dir / name).read_bytes() == _this_run(tmp_path, sizes, name)


class _FailingStream:
    def write(self, data):
        raise OSError('disk full')

    def flush(self):
        pass

    def close(self):
        pass


def test_tee_handler_write_failure(tmp_path):
    handler = log_tee.TeeFileHandler(tmp_path / 'copy.log', mode='a')
    handler.stream.close()
    handler.stream = _FailingStream()
    record = logging.LogRecord('test', logging.INFO, __file__, 0, 'message', None, None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for _ in range(3):
            handler.handle(record)

    archive_warnings = [w for w in caught if issubclass(w.category, run_archive.RsoptArchiveWarning)]
    assert len(archive_warnings) == 1
    assert 'copy.log' in str(archive_warnings[0].message)
    # Later records are dropped, and the file is not reopened
    assert handler.stream is None
    handler.close()


def test_copy_final_logs_false(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config, config_path = helpers.start(tmp_path, copy_final_logs=False)

    H, persis_info, _ = helpers.runner(config).run()
    run.cleanup(config_path, H, persis_info, config)

    run_dir = helpers.run_dir(tmp_path)
    for name in LOCAL_LOGS:
        assert (tmp_path / name).exists()
        assert not (run_dir / name).exists()
    assert list(run_dir.glob('*.npy')) == []
    assert (run_dir / run_archive.SNAPSHOT_DIRECTORY / run_archive.RUN_INFO_NAME).exists()


def test_end_of_run_copies_only_history(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_local_logs(tmp_path)
    config, config_path = helpers.start(tmp_path)

    H, persis_info, _ = helpers.runner(config).run()
    run.cleanup(config_path, H, persis_info, config)

    run_dir = helpers.run_dir(tmp_path)
    assert len(list(run_dir.glob('H_config_history_*.npy'))) == 1
    for name in LOCAL_LOGS:
        assert MARKER not in (run_dir / name).read_text()
    # The configuration file is only in the snapshot
    assert not (run_dir / config_path.name).exists()


def test_disable_log_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config, _ = helpers.start(tmp_path)
    runner = helpers.runner(config)
    configure_libE = runner._configure_libE

    def _configure_without_log_files():
        configure_libE()
        runner.libE_specs['disable_log_files'] = True

    runner._configure_libE = _configure_without_log_files

    with warnings.catch_warnings():
        warnings.simplefilter('error', run_archive.RsoptArchiveWarning)
        H, _, _ = runner.run()

    assert len(H) == len(helpers.X_VALUES)
    run_dir = helpers.run_dir(tmp_path)
    for name in LOCAL_LOGS:
        assert not (run_dir / name).exists()
    assert _libE_module().manager_logging_config is ORIGINAL_HOOK
