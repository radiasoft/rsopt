"""Early stopping for jobs run through the libEnsemble Executor.

A user supplied early stop function is called periodically, in a subprocess, while a job runs. It receives a copy of
the job dictionary `J`, runs in the simulation directory, and returns one of the `EarlyStop` values (or its string).

Users import `EarlyStop` from this module inside their early stop functions, so keep its imports light.
"""

import enum
import logging
import pathlib
import time
import typing
from rsopt.libe_tools import user_function

if typing.TYPE_CHECKING:
    from rsopt.configuration.schemas.setup import EarlyStopSetup

ERROR_FILE_NAME = "early_stop_error.txt"


class EarlyStop(str, enum.Enum):
    """Decisions an early stop function may return."""

    # Keep running the job
    CONTINUE = "continue"
    # Stop the job and treat it as finished successfully
    STOP_SUCCESS = "stop_success"
    # Stop the job and treat it as failed
    STOP_FAIL = "stop_fail"


class EarlyStopOnError(str, enum.Enum):
    """What to do when the early stop function raises or returns an invalid result."""

    # Kill the job and crash the run
    RAISE = "raise"
    # Kill the job and treat it as failed
    FAIL = "fail"


class EarlyStopError(Exception):
    """Early stop function raised or returned an invalid result while `on_error` is 'raise'."""


class EarlyStopMonitor:
    """Run the early stop function for one job, one check at a time.

    The first check starts `interval` seconds after the monitor is created, and each later check starts `interval`
    seconds after the previous one finished. The monitor only decides; the caller is responsible for the task.

    Args:
        early_stop_setup: (rsopt.configuration.schemas.setup.EarlyStopSetup) The job's early stop configuration.
        clock: (Callable) Returns the current time in seconds.
    """

    def __init__(
        self,
        early_stop_setup: "EarlyStopSetup",
        clock: typing.Callable[[], float] = time.monotonic,
    ):
        self.module_path, self.function_name = early_stop_setup.function
        self.interval = early_stop_setup.interval
        self.on_error = EarlyStopOnError(early_stop_setup.on_error)
        self.log = logging.getLogger("libensemble")
        self._clock = clock
        self._runner = user_function.UserFunctionProcess(
            self.module_path, self.function_name
        )
        self._last_end = clock()

    def update(self, J: dict) -> EarlyStop:
        """Advance the monitor. Call once per poll of the running task.

        Args:
            J: (dict) Job dictionary. The early stop function receives a copy.

        Returns:
            (EarlyStop) The decision from a check that just finished, otherwise `EarlyStop.CONTINUE`.

        Raises:
            EarlyStopError: if a check failed and `on_error` is 'raise'.
        """
        if self._runner.running:
            result = self._runner.poll()
            if result is None:
                return EarlyStop.CONTINUE
            self._last_end = self._clock()
            return self._decide(result)

        if self._clock() - self._last_end >= self.interval:
            self._runner.start(J)

        return EarlyStop.CONTINUE

    def terminate(self) -> None:
        """Stop a check in flight, if any."""
        self._runner.terminate()

    def _decide(self, result: user_function.Result) -> EarlyStop:
        if not result.failed:
            try:
                return EarlyStop(result.value)
            except (ValueError, TypeError):
                message = (
                    f"Early stop function {self.function_name} from {self.module_path} returned "
                    f"{result.value!r}. It must return one of: {', '.join(repr(e.value) for e in EarlyStop)}"
                )
        else:
            message = f"Early stop function {self.function_name} from {self.module_path} failed:\n{result.error}"

        if self.on_error == EarlyStopOnError.RAISE:
            raise EarlyStopError(message)

        self.log.warning(
            f"{message}\nJob will be stopped and treated as failed (on_error: fail)"
        )
        pathlib.Path(ERROR_FILE_NAME).write_text(message)
        return EarlyStop.STOP_FAIL
