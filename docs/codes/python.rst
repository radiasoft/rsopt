.. _python_ref:

``python``
==========

Python code may be executed by rsopt when specified in the ``code`` field. When executed in serial all Python functions
is run by workers, natively in their existing process. rsopt also supports parallel execution of Python code, however,
in this case the supplied function is imported into a dynamically created Python module to be run in a subprocess that
can execute MPI commands.::

    codes:
        - python:
            setup:
                input_file: /a_path/a_module.py
                function: foo  # Name of a function in `input_file` to be executed
                execution_type: serial  # Choose execution mode

Required ``setup`` fields for ``python`` are:

* ``input_file``: The path to a Python module, either absolute or relative to execution directory.
* ``function``: Name of a function in `input_file` to be executed
* ``execution_type``: Method to use when executing the Python code. See :ref:`Execution Methods<exec_methods>` for accepted types.

Optional fields:

* ``serial_python_mode``: By default Python functions will be executed directly by the assigned Worker process. This is convenient from a speed-of-execution perspective but can cause problems in some cases. For example if the code being executed by the Job requires special cleanup between executions; or if you expect some Jobs to fail, this will result in rsopt exiting prematurely since the error will occur directly on the process. In these cases it can be useful to select an alternate mode.

    - `worker`: The default option. Python functions are executed directly by the worker process.
    - `process`: The worker will initiate a subprocess to run the function. Return values of the function will be automatically passed back to rsopt. This option should be selected if it is required that each simulation be initiated in a clean memory space. This option does carry the highest overhead.
    - `thread`: Run the function in a thread. Memory is still shared, but errors produced by the simulation function will normally not be fatal for the rsopt process. Overhead cost should normally be on par with `worker`.

``function`` Specification
--------------------------

*   **arguments**: Input for the Python function being evaluated from the ``function`` key is always provided as a ``dict`` composed of
    the union of the settings and parameters for the job.

*   **return value**: The return value must be a single floating number (or be castable by NumPy to a float)
    Output is handled differently depending on if ``execution_type``
    is a serial or parallel run mode. For serial the output of the function is passed to ``options.objective_function``
    if one was given. If no separate objective function was supplied the output is directly handed to the optimizer, if one
    is being used. If you are using a parallel execution then you must specify a function in ``options.objective_function``
    that will read output, saved to file, from ``function``.