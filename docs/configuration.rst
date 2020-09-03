Configuration Files
===================

A run in rsopt is governed by the configuration set by the user. The configuration may be set by function calls in a
Python script that will be executed to start the run. An alternate method is to write a YAML configuration file which
can dictate the run flow and options. The run is then started by calling from the terminal:

* ``rsopt optimize configuration your_configuration_file.yaml``

Configuration Structure
-----------------------
Every configuration file has two top level keys: ``codes`` and ``options``. The block under ``codes`` provides an
ordered list of the name of each code to be executed.::

    codes:
        - python:
            ...
        - elegant:
            ...
        - opal:
            ...
    options:
        ...

Each code has optional fields of ``settings`` and ``parameters``. The ``settings`` field should contain a dictionary
of names and values that will be passed to the code at execution. All setting values are passed unchanged every time
a code is executed. In contract, ``parameter`` specifies names and values that will be passed to the optimizer and
thus changed by the optimizer at every execution.::

    codes:
        - python:
            settings:
                # Settings are optional. Each key should correspond to a single value.
                a: 42.
                b: 21
                c: false
            parameters:
                # All parameters must have subfields of min, max, start
                x:
                    min: 1.
                    max: 3.
                    start: 2.
                y:
                    min: 400
                    max: 1000
                    start: 500
        - elegant:
            parameters:
                m:
                    min: 8
                    max: 20
                    start: 12
    options:
        ...

Every parameter given must have the fields: ``min``, ``max``, and ``start``. Which correspond to the minimum, maximum,
and starting values for that parameter. Depending on the software being run by rsopt (specified in ``options``), or
other run parameters (e.g. a run with just 1 step would begin at the start values, execute, and stop)
all of these values may be used at run, however, they must always be given in the configuration.

Execution Methods
-----------------
Under ``setup`` for each ``code`` an ``execution_type`` must be specified::

    codes:
        - python:
            - parameters:
                ...
            - settings:
                ...
            - setup:
                - execution_type: serial

Currently accepted execution modes are:

* ``serial``: Serial execution of the code

Accepted Codes
--------------
Currently accepted code names are:

* ``python``::

    codes:
        - python:
            setup:
                input_file: /a_path/a_module.py
                function: foo  # Name of a function in `input_file` to be executed
                execution_type: serial  # Choose execution mode

Required ``setup`` fields for ``python`` are:

* ``input_file``: The path to a Python module, either absolute or relative to execution directory.
* ``function``: Name of a function in `input_file` to be executed
* ``execution_type``: Method to use when executing the Python code. See Execution Methods for accepted types.
