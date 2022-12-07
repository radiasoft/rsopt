.. _elegant_ref:

``elegant``
===========

Basic Setup
-----------

The particle accelerator tracking code ``elegant`` [1]_ [2]_ has special support in rsopt provided by the Sirepo library.
Using Sirepo, rsopt can parse ``elegant`` command and lattice files, automatically replacing and updating values given
for parameters and settings with no additional work required by the user. An example setup is shown below

.. code-block:: yaml

    codes:
        - elegant:
            settings:
                bunched_beam.n_particles_per_bunch: 42.
                run_setup.element_visions: 1
                D1.CSR: 0
            parameters:
                Q1.K1:
                    min: -5.
                    max: 5.
                    start: 1.
                Q1.L:
                    min: 400e-3
                    max: 900e-3
                    start: 500e-3
                D1.L:
                    min: 0.5
                    max: 2.5
                    start: 1.0
            setup:
                input_file: elegant_command_file.ele
                execution_type: serial  # Choose execution mode

In the above example settings is being used to modify the bunched_beam command particle count and run_setup element_division field.
The last setting is modifying the value of the CSR attribute for an element in the lattice, D1.
The parameters are then used to vary the element Q1's length (L) and quadrupole strength (K1), and the length of
element D1.

In setup you only need to provide the command file name, though the corresponding lattice file used by your command file
should be located in the same directory. rsopt will handle reading and parsing both files during optimization or
parameter sweeps. If multiple workers can be used for the rsopt run then they will always work in separate directories for
each new job to prevent overwriting files.

Syntax for repeated commands
----------------------------

Some commands may appear repeatedly in an input file. In this case the command name should be followed by the position
of the command to be used (indexed to 1). For instance if the command file contained two :code:`alter_element` commands
controlling the voltage and phase of all cavities in an rf cell:

.. code-block::

    !1
    &alter_elements
      item = "VOLT",
      name = "L2CELL*",
      type = "RF*",
      value = 0.9,
      multiplicative = 1
    &end

    !2
    &alter_elements
      item = "PHASE",
      name = "L2CELL*",
      type = "RF*",
      value = 66.0,
    &end

The corresponding block in the rsopt configuration file could look like:

.. code-block:: yaml

    codes:
        - elegant:
            parameters:
            alter_elements.1.value: # Voltage L2
                min: 8.0
                max: 1.1
                start: 1.0
            alter_elements.2.value: # Phase L2
                min: 60.0
                max: 77.0
                start: 6.42e+01
            setup:
                input_file: elegant_command_file.ele
                execution_type: serial


.. _elegant_name_mangling:

Output file name mangling
-------------------------

When ``elegant`` input files are written by the Sirepo parser at run time output file names will be changed in the
rsopt run directories (your original input file copy is not edited). File names are changed to always be in the form of
``command_name.parameter_name.sdds`` or ``element_name.parameter_name.sdds`` for commands (in a .ele file) or elements
(in a lattice file) respectively. For example::

    &run_setup
        sigma = "run1.sig"

Would become::

    &run_setup
        sigma = "run_setup.sigma.sdds"

This is important to be aware of when writing post-processing scripts and objective functions that will be used during
your rsopt run to ensure the correct file name is used.


Distribution Piping
-------------------

When running a job with a sequence of codes output particle distributions from OPAL  can be be automatically
piped to ``elegant`` and used as an ``sdds_beam`` input. In the settings section for the first code you must supply
the `output_distribution` parameter (keeping in mind possible :ref:`name mangling<elegant_name_mangling>`).
For example::

    codes:
        - opal
            setup:
                input_file: injector.in
                output_distribution: injector.h5  # will automatically use the final step in the file
                execution_type: parallel
                cores: 20
        - elegant:
            setup:
                input_file: elegant.ele
                input_distribution: from_injector.sdds  # distribution taken from OPAL will be written to this file
                execution_type: parallel
                cores: 4


Providing an objective value
----------------------------
When using ``elegant`` as the final code of an optimization run in rsopt you will need to provide an objective function in the
``options.objective_function`` field. The objective function is always executed in the same directory that ``elegant``
was run in for each new job and so can easily be used to read any output from ``elegant`` to perform required calculations.


.. [1]  M. Borland, ”elegant: A Flexible SDDS-Compliant Code for Accelerator Simulation,” AdvancedPhoton Source LS-287, September 2000.
.. [2]  Y. Wang and M. Borland, ”Pelegant: A Parallel Accelerator Simulation Code for Electron
        Generation and Tracking”, Proceedings of the 12th Advanced Accelerator Concepts Workshop,
        AIP Conf. Proc. 877, 241 (2006).
