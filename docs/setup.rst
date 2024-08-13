.. _options_ref:

Setup
=====
The `setup` block is required to be defined for each code in the `codes` list (see :doc:`Configuration<configuration>`).
The `setup` block handles specification of input files, execution method, and any pre/post processing functions which
will be run for the code. General options that can be used for setup of any code are described below. Special
consideration should be given when configuring :ref:`Python<codes/python>` jobs. Since rsopt is a Python program there are additional options
for how Python jobs should be executed. See :ref:`Python<codes/python>` for information.


General Setup Fields
--------------------

- `input_file` [str]:
    Path to the location of the input file for this code instance.
- `execution_type` [str]:
    Specify the method used to run the code. Availability may vary depending on resources being used. Available options
    are. Nested entries are additional fields that may be specified for the given mode.:

        * ``serial``: Serial execution of the code. If ``serial`` mode is used the simulation will always be executed on the same resources as the worker assigned the job. This can be a consideration if many workers will be running computationally intensive work.
        * ``parallel``: Parallel execution of the code with MPI. libEnsemble automatically detects MPI implementation and will automatically format input commands
        * ``shifter``: For use on NERSC. Runs inside of a Shifter container from the radiasoft/sirepo:prod image.
            - ``shifter_image`` can also be provided in Setup to request a particular image. The default is `radiasoft/sirepo:prod`.
        * ``rsmpi``: Special command for users who have servers registered to them on jupyter.radiasoft.org_. If rsmpi is being used for any code it must be used for all. The number of cores requested may vary from code to code though.

- `cores` [int]:
    Number of cores to use for parallel run modes (``parallel``, ``shifter``, ``rsmpi``). This is ignored for ``serial``.
- `force_executor` [bool]:
    If used with Python can be set to `True` to force a serial Python job to use an Executor. Otherwise Python jobs are
    run directly by the worker. Kept as a general setup field for backwards compatibility even though it will only
    have an effect when used with Python.
- `timeout` [float]:
    If a simulation does not complete in `timeout` seconds the simulation will be ended and marked failed. Not currently
    an option for ``serial`` Python simulations.
- `preprocess` [list(str, str)]
    Can be used to provide a Python function that will be run prior to the simulation starting. Given as a list with
    list(python_file_name, function_name_in_python_file) For instance:

    .. code-block:: yaml

      - opal:
          settings:
          parameters:
          setup:
            preprocess: [processes.py, my_preprocess]

    Where `my_preprocess` is a function defined in the file `processes.py`. For a full description of how to use
    pre and post processes see the :doc:`Job Dictionary<job_dictionary>` page.
- `postprocess` [list(str,str)]
    This is identical to `preprocess` except the `postprocess` will be run after the simulation ends.
    See the :doc:`Job Dictionary<job_dictionary>` page for details on writing postprocess functions.
- `code_arguments`:
    Can be used to provide arguments that will be given to the code execution
    in the Setup block at run time. For example:

    .. code-block:: yaml

      - opal:
          settings:
          parameters:
          setup:
            input_file: opal.in
            execution_type: serial
            code_arguments:
              "--info": 4
              "--help-command": Monitor
              "--git-revision":

    Would execute OPAL with `opal --info 4 --help-command Monitor --git-revision  opal.in`.
- `environment_variables` [dict]
    Mapping of environment variable names and values. Environment variables will be set before each simulation is
    started. This feature does not work with `python` code type but should work for any other code.

    .. code-block:: yaml

      - opal:
          settings:
          parameters:
          setup:
            environment_variables:
              MY_NEW_VAR: 4242
              ANOTHER_IS: "hi_there"

Templated Code Fields
---------------------
Additional specifications that can be given under `setup` for templated codes only, that is: elegant, MAD-X, OPAL, and
Genesis. In particular there is special handling in rsopt for converting particle phase space distribution files between these four codes.

- `input_distribution` [str]
    Name of the initial distribution file that the simulation expects to read in. If this simulation is not the first
    in the list of `codes` in the configuration file then the preceding code's `output_distribution` will be used to
    create the `input_distribution`.
- `output_distribution` [str]
    The name of the distribution file that simulation will produce at its completion. If the next `code` in the list
    has `input_distribution` specified the `input_distribution` will be created from this `output_distribution`.
- `ignored_files` [list(str)]
    This is a list of files that will be ignored when the input files for the simulation are parsed. Normally,
    rsopt verifies that all external resource files needed to run the simulation already exist
    (e.g. particle distributions, wakefields, field maps). Sometimes these files might be created by a preceding
    step in the rsopt run. In this case the file names can be added to this list and their existence will not be checked
    until the simulation starts. Files given under the `input_distribution` are automatically added to this list since
    rsopt will create them.

Serial Python Fields
--------------------
For serial Python an additional field can be given to specify how the Python function should be executed by the worker.

- `serial_python_mode` [str]
    Can be ``thread``, ``process``, or ``worker``. Default is ``worker``. See :ref:`Python<codes/python>` for a
    description of the options.


