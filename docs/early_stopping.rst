Early Stopping
==============

An early stop function lets you stop a running simulation as soon as its result is known, for instance when a
convergence criterion has been met, or when the simulation has clearly gone wrong. It is configured per code with
the `early_stop` field in `setup` (see :doc:`Setup<setup>`).

Early stopping is only available for jobs that run through a libEnsemble Executor. That is any code other than
Python, and Python jobs that set ``force_executor: True`` or use a parallel `execution_type`. Serial Python jobs that run
directly on the worker are rejected when the configuration is loaded.

Writing an early stop function
------------------------------

The function takes the :doc:`Job Dictionary<job_dictionary>` `J` as its only argument and returns one of the
following, either as the string or as the matching member of ``rsopt.early_stop.EarlyStop``:

- ``'continue'`` (``EarlyStop.CONTINUE``): Keep running.
- ``'stop_success'`` (``EarlyStop.STOP_SUCCESS``): Stop the simulation and continue as if it finished normally.
- ``'stop_fail'`` (``EarlyStop.STOP_FAIL``): Stop the simulation and treat it as failed.

Any other return value is an error and is handled according to `on_error`, as is an exception raised by the function.

The function runs in the simulation's directory, so it can read any output the simulation has written so far.
For example, to stop once the simulation's log file reports convergence, or as soon as a NaN appears in it:

.. code-block:: python
   :linenos:

   # early_stop.py
   import pathlib

   def check_run(J):
       log = pathlib.Path('run.log')
       if not log.exists():
           return 'continue'
       text = log.read_text()
       if 'converged' in text:
           return 'stop_success'
       if 'NaN' in text:
           return 'stop_fail'
       return 'continue'

.. code-block:: yaml

  - elegant:
      setup:
        input_file: run.ele
        execution_type: serial
        early_stop:
          function: [early_stop.py, check_run]
          interval: 30

What to know when writing an early stop function
------------------------------------------------

Each check runs the function in a new Python process. As a result:

- `J` is a copy. Changes made to it are discarded and are not seen by later checks, postprocess functions, or the
  objective function.
- Module level (global) variables do not carry over from one check to the next. To keep state between checks, write
  it to a file in the current directory (the simulation directory) and read it back on the next check.
- The function file is loaded from its path. Other modules that sit next to it are not automatically importable from
  the simulation directory. This is the same as for pre and postprocess functions.
- The function runs with the same environment variables as the simulation, including any GPU restriction such as
  ``CUDA_VISIBLE_DEVICES``.
- If you start rsopt from your own Python script, rather than with the ``rsopt`` command, put the code that starts
  the run under ``if __name__ == '__main__':``. Python re-imports the main script in each new process, and without
  this guard that would start the run again.

When a check returns ``'stop_success'`` or ``'stop_fail'`` the simulation is killed: it is sent SIGTERM, then SIGKILL
if it is still running 60 seconds later. Output files may therefore be incomplete after a ``'stop_success'``. If the
simulation code supports stopping itself cleanly, for instance by watching for a stop file, a better pattern is to
have the early stop function create that file and return ``'continue'``, letting the code finish and write its output
normally.

Only one check runs at a time. A slow check delays the next one but never delays the job's `timeout`, which is enforced
as usual. A check that is still running when the simulation ends is stopped.

Every early stop is recorded in `ensemble.log` along with the sim_id. In `libE_stats.txt` an early stop with
``'stop_success'`` is reported as ``Completed`` and one with ``'stop_fail'`` as ``Task Failed during run``.

Errors
------

`on_error` decides what happens if the function raises an exception or returns anything other than the values above.

- ``raise`` (default): The simulation is killed and the error, including the traceback from the early stop function,
  ends the whole rsopt run. This makes mistakes in the function obvious instead of letting them silently turn every
  simulation into a penalty value.
- ``fail``: The simulation is killed and treated as failed (the same as ``'stop_fail'``). The error is logged and
  written to `early_stop_error.txt` in the simulation directory.
