.. _user_ref:

``user``
===========

Can be used to run any command line executable through rsopt.



user setup commands
-------------------
These are special commands that must be included in the ``setup`` portion of the configuration file for ``user``.

* ``input_file``: Name of the input file that should be used when program is executed. Can be an existing file,
    in which case it will be copied into the run directory - or the name of a file included in ``file_mapping``,
    in which case it is created dynamically at run time.
    (``input_file`` is also used by other code types, but is listed here for clarity)

* ``run_command``: Executable to be called when program is run. rsopt will check for the executable in the run directory. If the executable is not found in the run directory the system PATH will be checked. The full path to the executable may also be provided.

* ``file_definitions``: Python module that contains each file required by the user program to be generated at for each
    job. Each file should be entered as a string with entries that will be formatted by rsopt at run time. The variable
    name for each string should be listed in ``file_mapping``.

* ``file_mapping``: A mapping that describes how the variables from ``file_definitions`` will be written to files
    at run time for each job. The keys of the dictionary should be the variables from ``file_defitions``. The value
    of each key should be the desired file name without any additional path information. rsopt will handle the path
    setup for the files.

The usual setup for serial or parallel execution may also be included in ``setup`` with ``user``. See
* :ref:`Execution Methods<exec_methods>` for a description of these options.