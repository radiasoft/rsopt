.. _madx_ref:

``MAD-X``
===========

Basic Setup
-----------

The code MAD-X [1]_ [2]_ is widely used for particle accelerator simulation and design.
Special support for MAD-X is in rsopt provided by the Sirepo library.
Using Sirepo, rsopt can parse MAD-X command and lattice files, automatically replacing and updating values given
for parameters and settings with no additional work required by the user. An example setup is shown below

.. code-block:: yaml

    codes:
        - madx:
            settings:
                TWISS.ALFX: 42.42
                BEAM.ENERGY: 5.05
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
                input_file: beamline_file.madx
                execution_type: serial

In the above example `settings` is being used to modify the twiss command alfx field and beam energy to new values for
every simulation.
The `parameters` are then used to vary the element Q1's length (L) and quadrupole strength (K1), and the length of
element D1. rsopt will handle reading and parsing of the input file and modify the appropriate values in new files created
for optimization and parameter sweeps. If multiple workers can be used for the rsopt run then they will always work in
separate directories for each new job to prevent overwriting files.

Syntax for repeated commands
----------------------------

Some commands may appear repeatedly in an input file. In this case the command name should be followed by the position
of the command to be used (indexed to 1). For instance if the command file contained two :code:`twiss` commands for
different lines:

.. code-block::

    !1
    twiss,alfx=42.,betx=40.0,bety=20.0,file="twissl1.file.tfs",line=L1;

    !2
    twiss,alfx=32.,betx=30.0,bety=20.0,file="twissl2.file.tfs",line=L2;

The corresponding block in the rsopt configuration file could look like:

.. code-block:: yaml

    codes:
        - madx:
            parameters:
            twiss.1.alfx:
                min: 8.0
                max: 1.1
                start: 1.0
            twiss.2.betx:
                min: 15.0
                max: 77.0
                start: 6.42e+01
            setup:
                input_file: madx_file.madx
                execution_type: serial


.. _madx_name_mangling:

Output file name mangling
-------------------------

When MAD-X input files are written by the Sirepo parser at run time output file names will be changed in the
rsopt run directories (your original input file copy is not edited). File names are changed to always be in the form of
``command_name.file.extension``. For example::

    twiss,alfx=42.,betx=40.0,bety=20.0,file="twissl1.tfs",line=L1;

Would become::

    twiss,alfx=42.,betx=40.0,bety=20.0,file="twissl1.file.tfs",line=L1;

This is important to be aware of when writing post-processing scripts and objective functions that will be used during
your rsopt run to ensure the correct file name is used.

Providing an objective value
----------------------------
When using MAD-X as the final code of an optimization run in rsopt you will need to provide an objective function in the
``options.objective_function`` field. The objective function is always executed in the same directory that MAD-X
was run in for each new job and so can easily be used to read any output from MAD-X to perform required calculations.


.. [1]  Grote, H., and F. Schmidt. "MAD-X-an upgrade from MAD8." In Proceedings of the 2003 Particle Accelerator Conference, vol. 5, pp. 3497-3499. IEEE, 2003.
.. [2]  https://mad.web.cern.ch/mad/
