"""run_dir ownership and the startup snapshot (rsopt.run_archive).

Run from inside `tests/`.
"""
import re
import warnings
import pytest
from ruamel.yaml import YAML
from rsopt import run
from rsopt import run_archive
from rsopt.libe_tools import optimizer
import archive_helpers as helpers


def _load_yaml(path):
    return YAML(typ='safe').load(path)


def _snapshot_dir(work_dir):
    return helpers.run_dir(work_dir) / run_archive.SNAPSHOT_DIRECTORY


# Run directory ownership

def test_startup_check_non_empty_run_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    planted = tmp_path / helpers.RUN_DIR_NAME / 'planted.txt'
    planted.parent.mkdir()
    planted.write_text('existing output')
    config_path = helpers.write_config(tmp_path)

    with pytest.raises(run_archive.RunDirectoryError, match=re.escape('[startup check]')) as e:
        run.startup_sequence(helpers.parse_config(config_path), config_path)

    assert str(helpers.run_dir(tmp_path)) in str(e.value)
    assert str(config_path.resolve()) in str(e.value)
    assert planted.read_text() == 'existing output'
    assert list(planted.parent.iterdir()) == [planted]
    assert not (tmp_path / 'ensemble.log').exists()


def test_startup_check_run_dir_is_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / helpers.RUN_DIR_NAME).write_text('not a directory')
    config_path = helpers.write_config(tmp_path)

    with pytest.raises(run_archive.RunDirectoryError, match=re.escape('[startup check]')):
        run.startup_sequence(helpers.parse_config(config_path), config_path)


@pytest.mark.parametrize('make_empty_dir', [False, True])
def test_startup_check_passes_and_resolves_run_dir(tmp_path, monkeypatch, make_empty_dir):
    monkeypatch.chdir(tmp_path)
    if make_empty_dir:
        (tmp_path / helpers.RUN_DIR_NAME).mkdir()

    config, config_path = helpers.start(tmp_path)

    assert config.options.run_dir == str(helpers.run_dir(tmp_path))
    assert config.config_path == config_path.resolve()


def test_pre_launch_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config, _ = helpers.start(tmp_path)
    planted = helpers.run_dir(tmp_path) / 'planted.txt'
    planted.parent.mkdir()
    planted.write_text('appeared after startup')

    with pytest.raises(run_archive.RunDirectoryError, match=re.escape('[pre-launch check]')) as e:
        helpers.runner(config).run()

    assert str(helpers.run_dir(tmp_path)) in str(e.value)
    # No snapshot, logs, or sim directories were written
    assert list(planted.parent.iterdir()) == [planted]
    assert not (tmp_path / 'ensemble.log').exists()


def test_existing_empty_run_dir_is_used(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    helpers.run_dir(tmp_path).mkdir()
    config, _ = helpers.start(tmp_path)

    H, _, _ = helpers.runner(config).run()

    assert len(H) == len(helpers.X_VALUES)
    assert len(list(helpers.run_dir(tmp_path).glob('worker*/sim*'))) == len(helpers.X_VALUES)
    assert (_snapshot_dir(tmp_path) / run_archive.RUN_INFO_NAME).exists()


def test_clean_work_dir_removed():
    with pytest.raises(TypeError):
        optimizer.libEnsembleOptimizer.run(None, clean_work_dir=True)


def test_archive_run_skipped_on_worker_rank(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config, _ = helpers.start(tmp_path)
    config.is_manager = False

    with run_archive.archive_run(config):
        pass

    assert not helpers.run_dir(tmp_path).exists()


# Snapshot

def test_snapshot_contents(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config, config_path = helpers.start(tmp_path)

    helpers.runner(config).run()

    snapshot_dir = _snapshot_dir(tmp_path)
    assert (snapshot_dir / config_path.name).read_bytes() == config_path.read_bytes()
    resolved = _load_yaml(snapshot_dir / run_archive.RESOLVED_CONFIG_NAME)
    assert resolved['options']['software'] == 'mesh_scan'
    run_info = _load_yaml(snapshot_dir / run_archive.RUN_INFO_NAME)
    assert run_info['run_info_version'] == run_archive.RUN_INFO_VERSION
    assert run_info['versions']['libensemble']
    assert run_info['rsopt']['run_dir'] == str(helpers.run_dir(tmp_path))
    assert run_info['rsopt']['config_file'] == str(config_path.resolve())
    assert run_info['snapshot_errors'] == []
    packages = (snapshot_dir / run_archive.PACKAGES_NAME).read_text().lower().splitlines()
    assert any(line.startswith('libensemble==') for line in packages)


def test_snapshot_without_config_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = helpers.parse_config(helpers.write_config(tmp_path))

    with pytest.warns(run_archive.RsoptArchiveWarning, match='configuration file path is not known'):
        H, _, _ = helpers.runner(config).run()

    assert len(H) == len(helpers.X_VALUES)
    run_info = _load_yaml(_snapshot_dir(tmp_path) / run_archive.RUN_INFO_NAME)
    assert run_info['rsopt']['config_file'] is None
    # run_dir is resolved even though startup_sequence was skipped
    assert run_info['rsopt']['run_dir'] == str(helpers.run_dir(tmp_path))


def test_snapshot_piece_failure_does_not_stop_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config, _ = helpers.start(tmp_path)

    def _broken(*args):
        raise RuntimeError('resolved config failure')

    monkeypatch.setattr(run_archive, '_write_resolved_config', _broken)

    with pytest.warns(run_archive.RsoptArchiveWarning, match=run_archive.RESOLVED_CONFIG_NAME):
        H, _, _ = helpers.runner(config).run()

    assert len(H) == len(helpers.X_VALUES)
    run_info = _load_yaml(_snapshot_dir(tmp_path) / run_archive.RUN_INFO_NAME)
    assert [e['item'] for e in run_info['snapshot_errors']] == [run_archive.RESOLVED_CONFIG_NAME]
    assert 'resolved config failure' in run_info['snapshot_errors'][0]['error']


def test_write_yaml_atomic(tmp_path):
    path = tmp_path / 'data.yml'

    run_archive.write_yaml_atomic(path, {'a': 1})
    run_archive.write_yaml_atomic(path, {'b': 2})

    assert _load_yaml(path) == {'b': 2}
    assert sorted(p.name for p in tmp_path.iterdir()) == ['data.yml']


def test_scheduler_environment_allow_list(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('SLURM_JOB_ID', '12345')
    monkeypatch.setenv('MY_SECRET', 'do-not-record')
    config, _ = helpers.start(tmp_path)
    helpers.run_dir(tmp_path).mkdir()

    with warnings.catch_warnings():
        warnings.simplefilter('error', run_archive.RsoptArchiveWarning)
        run_archive.write_snapshot(config, helpers.run_dir(tmp_path))

    run_info_path = _snapshot_dir(tmp_path) / run_archive.RUN_INFO_NAME
    scheduler_environment = _load_yaml(run_info_path)['scheduler_environment']
    assert scheduler_environment['SLURM_JOB_ID'] == '12345'
    assert 'MY_SECRET' not in scheduler_environment
    assert all(name.startswith(run_archive.SCHEDULER_ENVIRONMENT_PREFIXES)
               or name in run_archive.SCHEDULER_ENVIRONMENT_NAMES for name in scheduler_environment)
    assert 'do-not-record' not in run_info_path.read_text()
