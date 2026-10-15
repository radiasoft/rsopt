"""Live copy ("tee") of the libEnsemble logs into run_dir.

libEnsemble appends `ensemble.log` and `libE_stats.txt` in the working directory across runs. While a run is in
progress this module also writes the current run's log records into the top of run_dir, so run_dir holds the logs of
its own run even if the run is aborted.

This is the only place in rsopt that depends on libEnsemble's internal logging setup:
`libensemble.libE.manager_logging_config` opens the log file handlers on the manager, and
`libensemble.comms.logs.LogConfig.config` holds the logger names and file names. The hook is wrapped for the duration
of the `libE()` call to attach a second file handler to each logger. If the hook cannot be used, the current run's
portion of the local logs is copied into run_dir when the run ends instead.
"""
import contextlib
import importlib
import logging
import pathlib
import warnings
from rsopt import run_archive

_HOOK_NAME = 'manager_logging_config'
# (LogConfig attribute holding the logger name, LogConfig attribute holding the local file name)
_LOG_ATTRIBUTES = (('name', 'filename'), ('stats_name', 'stat_filename'))
_DEFAULT_LOCAL_NAMES = ('ensemble.log', 'libE_stats.txt')


def _warn(message: str) -> None:
    warnings.warn(message, run_archive.RsoptArchiveWarning, stacklevel=2)


class TeeFileHandler(logging.FileHandler):
    """File handler for the run_dir copy of a log.

    If writing fails, warns once and stops writing, so that a problem with run_dir never interrupts the run or the
    local log.
    """

    def __init__(self, *args, **kwargs):
        self._failed = False
        super().__init__(*args, **kwargs)

    def emit(self, record):
        if self._failed:
            return
        super().emit(record)

    def handleError(self, record):
        # Do not log through the libensemble logger from here, it would recurse into this handler
        if self._failed:
            return
        self._failed = True
        warnings.warn(run_archive.RsoptArchiveWarning(
            f'Writing to {self.baseFilename} failed. The copy of this log in run_dir stops here; '
            f'the log in the working directory continues.'
        ))
        try:
            self.close()
        except Exception:
            pass


class _TeedLog:
    """State of the run_dir copy of one libEnsemble log file."""

    def __init__(self, logger_name: str, local_path: pathlib.Path, run_dir: pathlib.Path):
        self.logger_name = logger_name
        self.local_path = local_path
        self.target = run_dir / local_path.name
        # This run's output starts here in the local file, which libEnsemble opens in append mode
        self.offset = _file_size(local_path)
        self.handler = None
        self.hook_called = False
        self.fallback = False

    @property
    def is_local_file(self) -> bool:
        """The run_dir copy would be the local file itself"""
        return _same_file(self.target, self.local_path)

    def attach(self) -> None:
        """Copy this run's output so far into the run_dir copy and attach a handler that writes the rest."""
        self.hook_called = True
        if self.is_local_file:
            return
        logger = logging.getLogger(self.logger_name)
        source = _find_file_handler(logger, self.local_path)
        if source is None:
            _warn(f'Could not find the libEnsemble handler for {self.local_path}. It will be copied into run_dir '
                  f'when the run ends.')
            self.fallback = True
            return
        try:
            source.flush()
            _copy_from_offset(self.local_path, self.offset, self.target)
            handler = TeeFileHandler(self.target, mode='a', encoding=source.encoding)
        except OSError as e:
            _warn(f'Could not open {self.target} to copy {self.local_path} into run_dir: {e!r}. '
                  f'It will be copied into run_dir when the run ends.')
            self.fallback = True
            return
        handler.setFormatter(source.formatter)
        for f in source.filters:
            handler.addFilter(f)
        handler.setLevel(source.level)
        # Appended, never first: libEnsemble's exit_logger closes handlers[0] of the stats logger
        logger.addHandler(handler)
        self.handler = handler

    def detach(self) -> None:
        """Remove and close the handler. Safe to repeat."""
        if self.handler is None:
            return
        handler, self.handler = self.handler, None
        logging.getLogger(self.logger_name).removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    def copy_at_exit(self) -> None:
        """Fallback: copy this run's portion of the local log into run_dir."""
        if self.is_local_file:
            return
        if _file_size(self.local_path) <= self.offset:
            # Nothing was logged in this run, e.g. libEnsemble log files are disabled
            return
        try:
            _copy_from_offset(self.local_path, self.offset, self.target)
        except OSError as e:
            _warn(f'Could not copy {self.local_path} into run_dir: {e!r}')


def _file_size(path: pathlib.Path) -> int:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def _same_file(a: pathlib.Path, b: pathlib.Path) -> bool:
    return a.resolve() == b.resolve()


def _copy_from_offset(source: pathlib.Path, offset: int, target: pathlib.Path) -> None:
    with open(source, 'rb') as src, open(target, 'wb') as dst:
        src.seek(offset)
        while chunk := src.read(1 << 20):
            dst.write(chunk)


def _find_file_handler(logger: logging.Logger, local_path: pathlib.Path) -> logging.FileHandler or None:
    """The FileHandler on `logger` that writes `local_path`, if any."""
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and not isinstance(handler, TeeFileHandler):
            if _same_file(pathlib.Path(handler.baseFilename), local_path):
                return handler
    return None


def _locate_hook():
    """Returns (libensemble.libE module, original hook, LogConfig.config), or None if they do not look as expected."""
    try:
        # import_module, not `import libensemble.libE`: the libensemble package may bind the name libE to the function
        libE_module = importlib.import_module('libensemble.libE')
        logs_module = importlib.import_module('libensemble.comms.logs')
    except ImportError:
        return None
    original = getattr(libE_module, _HOOK_NAME, None)
    log_config = getattr(getattr(logs_module, 'LogConfig', None), 'config', None)
    if not callable(original) or log_config is None:
        return None
    if not all(isinstance(getattr(log_config, a, None), str) for pair in _LOG_ATTRIBUTES for a in pair):
        return None
    return libE_module, original, log_config


def _fallback_local_names() -> tuple[str, str]:
    """Local log file names when the hook cannot be used: from LogConfig if possible, else libEnsemble's defaults."""
    try:
        log_config = importlib.import_module('libensemble.comms.logs').LogConfig.config
        names = tuple(getattr(log_config, filename) for _, filename in _LOG_ATTRIBUTES)
        if all(isinstance(name, str) for name in names):
            return names
    except Exception:
        pass
    return _DEFAULT_LOCAL_NAMES


@contextlib.contextmanager
def tee_libe_logs(run_dir: pathlib.Path):
    """Write the libEnsemble logs into run_dir, as well as the working directory, during the block.

    Wrap the `libE()` call with this. The local logs are not changed: libEnsemble keeps appending to them. The run_dir
    copies hold only the output of this run.

    Args:
        run_dir: (pathlib.Path) Existing directory to write `ensemble.log` and `libE_stats.txt` into.
    """
    run_dir = pathlib.Path(run_dir)
    located = _locate_hook()
    if located is None:
        _warn('Could not attach to libEnsemble logging; logs will be copied into run_dir when the run ends.')
        logs = [_TeedLog('', pathlib.Path(name).resolve(), run_dir) for name in _fallback_local_names()]
        for log in logs:
            log.fallback = True
        try:
            yield
        finally:
            for log in logs:
                log.copy_at_exit()
        return

    libE_module, original, log_config = located
    logs = [_TeedLog(getattr(log_config, name), pathlib.Path(getattr(log_config, filename)).resolve(), run_dir)
            for name, filename in _LOG_ATTRIBUTES]

    def wrapped(*args, **kwargs):
        exit_logger = original(*args, **kwargs)
        for log in logs:
            try:
                log.attach()
            except Exception as e:
                # Never let the tee break the run
                _warn(f'Could not tee {log.local_path} into run_dir: {e!r}. It will be copied when the run ends.')
                log.detach()
                log.fallback = True

        def wrapped_exit():
            try:
                # First, so the final "Exiting ensemble" record reaches both copies
                exit_logger()
            finally:
                for log in logs:
                    log.detach()

        return wrapped_exit

    setattr(libE_module, _HOOK_NAME, wrapped)
    try:
        yield
    finally:
        setattr(libE_module, _HOOK_NAME, original)
        for log in logs:
            log.detach()
        for log in logs:
            if log.fallback or not log.hook_called:
                log.copy_at_exit()
