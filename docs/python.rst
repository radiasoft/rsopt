.. _python_ref:

``python``
----------

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
