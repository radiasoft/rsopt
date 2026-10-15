"""Ownership and archiving of the run directory (`options.run_dir`).

rsopt never writes into existing output: `run_dir` must be absent or empty. It is checked when rsopt starts
(`check_run_dir_at_startup`) and again just before libEnsemble launches (`check_run_dir_before_launch`). rsopt then
creates `run_dir` itself and writes a snapshot of the run (configuration, versions, machine information) into
`run_dir/rsopt_snapshot/` before libEnsemble starts, so the record exists even if the run is aborted.

The libEnsemble logs are teed into `run_dir` by `rsopt.libe_tools.log_tee`, which is the only module that depends on
libEnsemble's logging internals.
"""
import contextlib
import datetime
import getpass
import importlib.metadata
import os
import pathlib
import platform
import shutil
import socket
import subprocess
import sys
import warnings
from ruamel.yaml import YAML
from rsopt.libe_tools import log_tee

SNAPSHOT_DIRECTORY = 'rsopt_snapshot'
RESOLVED_CONFIG_NAME = 'resolved_config.yml'
RUN_INFO_NAME = 'run_info.yml'
PACKAGES_NAME = 'packages.txt'
RUN_INFO_VERSION = 1

# Packages whose versions are always recorded in run_info.yml. The full list is in packages.txt.
_RECORDED_VERSIONS = ('rsopt', 'libensemble', 'numpy', 'pydantic', 'sirepo')

# Only these environment variables are recorded. Never capture the full environment, it can contain secrets.
SCHEDULER_ENVIRONMENT_PREFIXES = ('SLURM_', 'PBS_', 'LSB_', 'FLUX_')
SCHEDULER_ENVIRONMENT_NAMES = ('NERSC_HOST', 'CUDA_VISIBLE_DEVICES', 'OMP_NUM_THREADS')

_GIT_TIMEOUT = 5

_RESOLVED_CONFIG_HEADER = (
    '# Configuration as resolved by rsopt, including default values.\n'
    '# This file is informational only and is not intended to be run by rsopt.\n'
    '# The configuration file as given to rsopt is also in this directory.\n'
)


class RunDirectoryError(Exception):
    """run_dir already holds output (or is not a directory) and the run cannot use it."""


class RsoptArchiveWarning(UserWarning):
    """Part of the run archive (snapshot or log copy) could not be written. The run itself continues."""


def resolve_run_dir(options) -> pathlib.Path:
    """Absolute path of `options.run_dir`. Relative paths are resolved against the working directory.

    Args:
        options: (rsopt.configuration.schemas.options.Options) Options holding `run_dir`.

    Returns:
        pathlib.Path
    """
    return pathlib.Path(options.run_dir).expanduser().resolve()


def _run_dir_problem(path: pathlib.Path) -> str or None:
    """Returns why `path` cannot be used as run_dir, or None if it is absent or an empty directory."""
    if not path.exists():
        return None
    if not path.is_dir():
        return 'not_a_directory'
    if any(path.iterdir()):
        return 'not_empty'
    return None


def check_run_dir_at_startup(path: pathlib.Path, config_path: pathlib.Path or None = None) -> None:
    """Check that run_dir is absent or empty when rsopt starts.

    Args:
        path: (pathlib.Path) Absolute path of run_dir.
        config_path: (pathlib.Path or None) Configuration file that set run_dir, used in the error message.

    Raises:
        RunDirectoryError: if run_dir exists and is not an empty directory.
    """
    problem = _run_dir_problem(path)
    if problem is None:
        return
    state = {
        'not_a_directory': 'already exists and is not a directory',
        'not_empty': 'already exists and is not empty',
    }[problem]
    where = f' in {config_path}' if config_path else ''
    raise RunDirectoryError(
        f"[startup check] run_dir '{path}' {state}. rsopt never writes into existing output. "
        f"Delete or rename that {'directory' if problem == 'not_empty' else 'file'}, "
        f"or set a different `options.run_dir`{where}."
    )


def check_run_dir_before_launch(path: pathlib.Path) -> None:
    """Check again, just before libEnsemble launches, that run_dir is absent or empty.

    Args:
        path: (pathlib.Path) Absolute path of run_dir.

    Raises:
        RunDirectoryError: if run_dir exists and is not an empty directory.
    """
    problem = _run_dir_problem(path)
    if problem is None:
        return
    state = {
        'not_a_directory': 'is now a file',
        'not_empty': 'now contains files',
    }[problem]
    raise RunDirectoryError(
        f"[pre-launch check] run_dir '{path}' was absent or empty when checked at startup but {state}, "
        f"so the run was stopped just before libEnsemble launched. Another process may be using this "
        f"{'directory' if problem == 'not_empty' else 'path'}. Nothing was written to it. "
        f"Delete or rename it, or set a different `options.run_dir`, and rerun."
    )


def write_yaml_atomic(path: pathlib.Path, data) -> None:
    """Write `data` as YAML to `path`, replacing any existing file in one step.

    The data is dumped to `<name>.tmp` in the same directory and then moved over `path`, so readers never see a
    partially written file.

    Args:
        path: (pathlib.Path) File to write.
        data: Data to dump. Must be representable by the ruamel safe dumper.
    """
    path = pathlib.Path(path)
    tmp_path = path.with_name(path.name + '.tmp')
    try:
        with open(tmp_path, 'w') as ff:
            _yaml().dump(data, ff)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _yaml() -> YAML:
    yaml = YAML(typ='safe')
    yaml.default_flow_style = False
    return yaml


def _warn(message: str) -> None:
    warnings.warn(message, RsoptArchiveWarning, stacklevel=3)


def write_snapshot(config, run_dir: pathlib.Path) -> pathlib.Path or None:
    """Write the startup snapshot of the run into `run_dir/rsopt_snapshot/`.

    Failures never abort the run. Each piece that cannot be written issues an `RsoptArchiveWarning` and is recorded
    under `snapshot_errors` in `run_info.yml`.

    Args:
        config: (rsopt.configuration.schemas.configuration.ConfigurationSample) Configuration of the run.
        run_dir: (pathlib.Path) Absolute path of run_dir, which must already exist.

    Returns:
        pathlib.Path of the snapshot directory, or None if it could not be created.
    """
    snapshot_dir = pathlib.Path(run_dir) / SNAPSHOT_DIRECTORY
    try:
        snapshot_dir.mkdir()
    except Exception as e:
        _warn(f'Could not create the snapshot directory {snapshot_dir}, no snapshot will be written: {e!r}')
        return None

    errors = []

    def _attempt(item, func, *args):
        try:
            func(*args)
        except Exception as e:
            _warn(f'Could not write {item} to the run snapshot in {snapshot_dir}: {e!r}')
            errors.append({'item': item, 'error': repr(e)})

    if config.config_path is None:
        _warn('The configuration file path is not known, so the configuration file is not saved in the run '
              f'snapshot in {snapshot_dir}. Pass the path to rsopt.run.startup_sequence to save it.')
    else:
        _attempt('config_file', _copy_config_file, config.config_path, snapshot_dir)
    _attempt(RESOLVED_CONFIG_NAME, _write_resolved_config, config, snapshot_dir)
    _attempt(PACKAGES_NAME, _write_packages, snapshot_dir)
    # TODO: snapshot input-file dependencies into rsopt_snapshot/inputs/ once `rsopt pack`'s dependency collection
    #  works with the current Code schema for all codes.

    # Written last so it can record errors from the other pieces
    try:
        write_yaml_atomic(snapshot_dir / RUN_INFO_NAME, collect_run_info(config, run_dir, errors))
    except Exception as e:
        _warn(f'Could not write {RUN_INFO_NAME} to the run snapshot in {snapshot_dir}: {e!r}')

    return snapshot_dir


def _copy_config_file(config_path: pathlib.Path, snapshot_dir: pathlib.Path) -> None:
    config_path = pathlib.Path(config_path)
    shutil.copy2(config_path, snapshot_dir / config_path.name)


def _write_resolved_config(config, snapshot_dir: pathlib.Path) -> None:
    # by_alias=False: Options has both `record_interval` and `save_every_k_sims` (alias `record_interval`), which
    # would collide on one key if dumped by alias.
    data = config.model_dump(mode='json', by_alias=False)
    with open(snapshot_dir / RESOLVED_CONFIG_NAME, 'w') as ff:
        ff.write(_RESOLVED_CONFIG_HEADER)
        _yaml().dump(data, ff)


def _write_packages(snapshot_dir: pathlib.Path) -> None:
    packages = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata['Name']
        # The first distribution found for a name is the one that is imported
        if name and name.lower() not in packages:
            packages[name.lower()] = f'{name}=={distribution.version}'
    (snapshot_dir / PACKAGES_NAME).write_text(''.join(f'{packages[k]}\n' for k in sorted(packages)))


def collect_run_info(config, run_dir: pathlib.Path, snapshot_errors: list) -> dict:
    """Information about this run, the software versions, and the machine, for `run_info.yml`.

    A section that cannot be collected is set to None and its error is appended to `snapshot_errors`.

    Args:
        config: (rsopt.configuration.schemas.configuration.ConfigurationSample) Configuration of the run.
        run_dir: (pathlib.Path) Absolute path of run_dir.
        snapshot_errors: (list) Errors from writing the snapshot. Recorded in the result.

    Returns:
        dict
    """
    run_info = {
        'run_info_version': RUN_INFO_VERSION,
        'start_time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    sections = (
        ('rsopt', _rsopt_info, (config, run_dir)),
        ('versions', _versions, ()),
        ('source_control', _source_control, (config.config_path,)),
        ('machine', _machine, (config,)),
        ('scheduler_environment', _scheduler_environment, ()),
    )
    for name, func, args in sections:
        try:
            run_info[name] = func(*args)
        except Exception as e:
            _warn(f'Could not collect {name} for {RUN_INFO_NAME}: {e!r}')
            snapshot_errors.append({'item': f'{RUN_INFO_NAME}:{name}', 'error': repr(e)})
            run_info[name] = None
    run_info['snapshot_errors'] = snapshot_errors

    return run_info


def _rsopt_info(config, run_dir: pathlib.Path) -> dict:
    executor_type = config.executor_type
    return {
        'command_line': list(sys.argv),
        'working_directory': os.getcwd(),
        'config_file': str(config.config_path) if config.config_path else None,
        'run_dir': str(run_dir),
        'software': config.options.software,
        'nworkers': config.options.nworkers,
        'comms': config.comms,
        'executor_type': executor_type.value if executor_type is not None else None,
    }


def _package_version(name: str) -> str or None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _versions() -> dict:
    versions = {name: _package_version(name) for name in _RECORDED_VERSIONS}
    versions['python'] = platform.python_version()
    return versions


def _git(directory: pathlib.Path, *args) -> str:
    result = subprocess.run(['git', '-C', str(directory), *args], capture_output=True, text=True,
                            timeout=_GIT_TIMEOUT, check=True)
    return result.stdout


def _source_control(config_path: pathlib.Path or None) -> dict or None:
    """Git commit and dirty state of the configuration file's directory. None if it is not in a git repository."""
    directory = pathlib.Path(config_path).parent if config_path else pathlib.Path(os.getcwd())
    try:
        commit = _git(directory, 'rev-parse', 'HEAD').strip()
        dirty = bool(_git(directory, 'status', '--porcelain').strip())
    except (OSError, subprocess.SubprocessError):
        return None
    return {'commit': commit, 'dirty': dirty}


def _user() -> str or None:
    try:
        return getpass.getuser()
    except Exception:
        return None


def _machine(config) -> dict:
    if hasattr(os, 'sched_getaffinity'):
        cpus_available = len(os.sched_getaffinity(0))
    else:
        cpus_available = None
    return {
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
        'machine': platform.machine(),
        'cpu_count': os.cpu_count(),
        'cpus_available': cpus_available,
        'user': _user(),
        'pid': os.getpid(),
        'gpu_devices': config.options.gpu_options.devices,
    }


def _scheduler_environment() -> dict:
    return {name: value for name, value in sorted(os.environ.items())
            if name.startswith(SCHEDULER_ENVIRONMENT_PREFIXES) or name in SCHEDULER_ENVIRONMENT_NAMES}


@contextlib.contextmanager
def archive_run(config):
    """Prepare run_dir and archive the run around the libE() call.

    Checks run_dir again, creates it, writes the startup snapshot, and (if `options.copy_final_logs`) tees the
    libEnsemble logs into it for the duration of the block.

    Args:
        config: (rsopt.configuration.schemas.configuration.ConfigurationSample) Configuration of the run.

    Raises:
        RunDirectoryError: if run_dir is no longer absent or empty.
    """
    # TODO(MPI): config.is_manager is always True until MPI detection in run.startup_sequence is
    #  restored. Under MPI comms, worker ranks would otherwise see the manager's new directory and fail.
    if not config.is_manager:
        yield
        return
    run_dir = resolve_run_dir(config.options)
    check_run_dir_before_launch(run_dir)
    # Failure to create run_dir is fatal, unlike the rest of the archive
    run_dir.mkdir(parents=True, exist_ok=True)
    write_snapshot(config, run_dir)
    if config.options.copy_final_logs:
        with log_tee.tee_libe_logs(run_dir):
            yield
    else:
        yield
