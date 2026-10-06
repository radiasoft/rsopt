import dataclasses
import multiprocessing
import multiprocessing.connection
import multiprocessing.process
import os
import traceback
import typing
from rsopt import util

# User functions are reloaded from their file in the child, so they never need to be pickled. 'spawn' also avoids
# forking a libEnsemble worker that may be an MPI rank. Module level so tests can substitute a specific start method.
_mp_context = multiprocessing.get_context("spawn")
# Seconds to wait for a child to exit after it is asked to stop (or after it has sent its result)
_JOIN_TIMEOUT = 5.0


@dataclasses.dataclass
class Result:
    """Outcome of a user function call made in a subprocess.

    Attributes:
        value: Value returned by the function.
        error: Formatted traceback if the function raised, or a description of the failure if the child process
            ended without returning a result. None if the call succeeded.
    """

    value: typing.Any = None
    error: str | None = None

    @property
    def failed(self) -> bool:
        return self.error is not None


@dataclasses.dataclass
class _Call:
    """A call in flight: the child process and the receiving end of its result pipe."""

    process: multiprocessing.process.BaseProcess
    connection: multiprocessing.connection.Connection


def _child(module_path, function_name, environment, connection, args, kwargs):
    # Children do not inherit the parent's current environment under the 'forkserver' start method.
    # Apply it explicitly so settings, particularly CUDA_VISIBLE_DEVICES, always reach the function.
    os.environ.clear()
    os.environ.update(environment)
    try:
        function = getattr(util.run_path_as_module(module_path), function_name)
        # Raises here, before anything is written, if the return value cannot be pickled
        connection.send(Result(value=function(*args, **kwargs)))
    except BaseException:
        connection.send(Result(error=traceback.format_exc()))
    finally:
        connection.close()


class UserFunctionProcess:
    """Run a user function in a subprocess without blocking the caller.

    The function is loaded in the child from `module_path`, so it does not need to be picklable. Arguments and the
    return value must be picklable. Only one call may be in flight at a time.

    Args:
        module_path: (str) Absolute path to the file that defines the function.
        function_name: (str) Name of the function in that file.
    """

    def __init__(self, module_path: str, function_name: str):
        self.module_path = str(module_path)
        self.function_name = function_name
        self._call: _Call | None = None
        self._exitcode = None

    @property
    def running(self) -> bool:
        """True from `start` until the result is collected by `poll` or the call is ended by `terminate`."""
        return self._call is not None

    def start(self, *args, **kwargs) -> None:
        """Call the function in a new subprocess.

        Args:
            *args: Positional arguments passed to the function.
            **kwargs: Keyword arguments passed to the function.
        """
        if self.running:
            raise RuntimeError(
                f"A call to {self.function_name} from {self.module_path} is already running"
            )

        receiver, sender = _mp_context.Pipe(duplex=False)
        process = _mp_context.Process(
            target=_child,
            args=(
                self.module_path,
                self.function_name,
                dict(os.environ),
                sender,
                args,
                kwargs,
            ),
            daemon=True,
        )
        process.start()
        # Only the child holds the sending end, so the receiver sees EOF if the child dies without sending
        sender.close()
        self._call = _Call(process=process, connection=receiver)

    def poll(self) -> Result | None:
        """Collect the result of the call if it has finished. Never blocks waiting on the function.

        Returns:
            (Result or None) None while the function is running (or if no call was started), else the Result.
        """
        call = self._call
        if call is None:
            return None
        if not call.connection.poll() and call.process.is_alive():
            return None

        # Read before joining: a child blocked on writing a large result to the pipe would never exit
        try:
            result = call.connection.recv()
        except EOFError:
            result = None
        self._stop(call, terminate=False)

        if result is None:
            result = Result(
                error=f"Process running {self.function_name} from {self.module_path} "
                f"exited with code {self._exitcode} without returning a result"
            )
        return result

    def terminate(self) -> None:
        """Stop the call in flight, if any. Safe to call at any time."""
        if self._call is not None:
            self._stop(self._call, terminate=True)

    def _stop(self, call: _Call, terminate: bool) -> None:
        process = call.process
        if not terminate:
            process.join(_JOIN_TIMEOUT)
        if process.is_alive():
            process.terminate()
            process.join(_JOIN_TIMEOUT)
            if process.is_alive():
                process.kill()
                process.join()
        self._exitcode = process.exitcode
        process.close()
        call.connection.close()
        self._call = None
