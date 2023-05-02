import threading
import multiprocessing
from libensemble import message_numbers
from typing import Callable

SERIAL_MODE_DEFAULT = 'worker'
RESULT = 'result'
CODE = 'return_code'
_NULL_RESULT = 'xo9cHSVI35KmWc1V'


def _process_wrapper(function, queue, *args, **kwargs):
    result = function(*args, **kwargs)
    queue.put(result)


def run_process(function: Callable, *args, **kwargs) -> dict:
    """ Run function in a subprocess.

    If the function fails the result in the returned dictionary will be None.

    Args:
        function: (Callable) Function to be executed
        *args: (list) Arguments passed to the Python simulation function.
        **kwargs: (dict) Key word arguments passed to the Python simulation function.

    Returns:
        (dict) Dictionary with result of simulation (if any) and return code.
    """
    result_queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_process_wrapper,
                                args=(function, result_queue, *args), kwargs=kwargs)
    p.start()
    p.join()
    
    if p.exitcode != 0:
        return_code = message_numbers.TASK_FAILED
        result = None
    else:
        return_code = message_numbers.WORKER_DONE
        result = result_queue.get()
    
    return {RESULT: result, CODE: return_code}


def _thread_wrapper(function, container, *args, **kwargs):
    result = function(*args, **kwargs)
    container[0] = result


def run_thread(function: Callable, *args, **kwargs) -> dict:
    """ Run function in a thread.

    If the function fails the result in the returned dictionary will be None.

    Args:
        function: (Callable) Function to be executed
        *args: (list) Arguments passed to the Python simulation function.
        **kwargs: (dict) Key word arguments passed to the Python simulation function.

    Returns:
        (dict) Dictionary with result of simulation (if any) and return code.
    """
    container = [_NULL_RESULT]
    p = threading.Thread(target=_thread_wrapper,
                         args=(function, container, *args), kwargs=kwargs)
    p.start()
    p.join()

    if container[0] == _NULL_RESULT:
        return_code = message_numbers.TASK_FAILED
        result = None
    else:
        return_code = message_numbers.WORKER_DONE
        result = container[0]

    return {RESULT: result, CODE: return_code}


def run_worker(function: Callable, *args, **kwargs) -> dict:
    """ Run function in a subprocess.

    If the function has an error then rsopt with crash, and you don't need to about worry what is in the result.

    Args:
        function: (Callable) Function to be executed
        *args: (list) Arguments passed to the Python simulation function.
        **kwargs: (dict) Key word arguments passed to the Python simulation function.

    Returns:
        (dict) Dictionary with result of simulation (if any) and return code.
    """
    result = function(*args, **kwargs)

    # If function fails this return will not be reached so return_code is always success
    return {RESULT: result, CODE: message_numbers.WORKER_DONE}


SERIAL_MODES = {'process': run_process,
                'thread': run_thread,
                'worker': run_worker}
