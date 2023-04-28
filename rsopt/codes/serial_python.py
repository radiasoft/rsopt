import threading
import multiprocessing
from libensemble import message_numbers

SERIAL_MODE_DEFAULT = 'worker'
RESULT = 'result'
CODE = 'return_code'
_NULL_RESULT = 'xo9cHSVI35KmWc1V'


def _process_wrapper(function, queue, *args, **kwargs):
    result = function(*args, **kwargs)
    queue.put(result)


def run_process(function, *args, **kwargs):
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


def run_thread(function, *args, **kwargs):
    container = [_NULL_RESULT]
    p = threading.Thread(target=_thread_wrapper,
                         args=(function, container, *args), kwargs=kwargs)
    p.start()
    p.join()

    if container[0] == _NULL_RESULT:
        return_code = message_numbers.TASK_FAILED
    else:
        return_code = message_numbers.WORKER_DONE

    return {RESULT: container[0], CODE: return_code}


def run_worker(function, *args, **kwargs):
    result = function(*args, **kwargs)

    # If function fails this return will not be reached so return_code is always success
    return {RESULT: result, CODE: message_numbers.WORKER_DONE}


def serial_runner(serial_mode, function, *args, **kwargs) -> dict:
    return SERIAL_MODES[serial_mode](function, *args, **kwargs)


SERIAL_MODES = {'process': run_process,
                'thread': run_thread,
                'worker': run_worker}
