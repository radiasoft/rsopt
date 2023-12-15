.. _opal_ref:

``OPAL``
========

Basic Setup
-----------

The particle accelerator tracking code ``OPAL`` [1]_ [2]_ has special support in rsopt provided by the Sirepo library.
Using Sirepo, rsopt can parse ``OPAL`` input files, automatically replacing and updating values given
for parameters and settings with no additional work required by the user. An example setup is shown below:

.. code-block:: yaml

    codes:
        - opal:
            settings:
                distribution.tpulsefwhm: 0.5e-11
            parameters:
                FINSS_RGUN.LAG:
                    min: -0.070
                    max: -0.052
                    start: -0.06108
                FIND1_MSOL10.KS:
                    min: 0.195
                    max: 0.237
                    start: 0.206
            setup:
                execution_type: parallel
                cores: 4
                input_file: ctf3.in



In the above example settings is being used to modify the distribution command to change the initial bunch length.
While OPAL allows assignment of names to a number of commands (such as distribution, and fieldsolver) the rsopt parser
only looks for the command name.
The parameters are then used to vary the RFCAVITY `FINSS_RGUN`'s `LAG` value and SOLENOID `FIND1_MSOL10`'s strength.
For elements the name of the element should be used as the identifier.

In setup you only need to provide the input file name, there is a restriction on the parser that all OPAL input must be
within the given input file (the CALL command is not currently supported by the parser).
rsopt will handle reading and parsing both files during optimization or
parameter sweeps. If multiple workers can be used for the rsopt run then they will always work in separate directories for
each new job to prevent overwriting files.

Syntax for repeated commands
----------------------------

Some commands may appear repeatedly in an input file. In this case the command name should be followed by the position
of the command to be used (indexed to 1). For instance if the input file contained two :code:`DISTRIBUTION` commands:

.. code-block::

    // 1
    gen_dist: DISTRIBUTION, TYPE = FLATTOP,
            SIGMAR = 0.001*2,
            TPULSEFWHM = fwhm*2,
            NBIN = 9,
            EMISSIONSTEPS = 100,
            EMISSIONMODEL = NONE,
            EKIN = 0.55,
            EMITTED = True,
            WRITETOFILE = True;
    // 2
    vc_dist: DISTRIBUTION, TYPE = FROMFILE,
            FNAME = "laser.dist",
            EMITTED = TRUE,
            EMISSIONMODEL = None,
            NBIN = 9,
            EMISSIONSTEPS = 100,
            EKIN = 0.4;

If the :code:`gen_dist` :code:`DISTRIBUTION` were being used by OPAL
The corresponding block in the rsopt configuration file to use :code:`TPULSEFWHM` as an optimization parameter
would look like:

.. code-block:: yaml

    codes:
        - opal:
            parameters:
              DISTRIBUTION.1.TPULSEFWHM:
                min: 0.8e-11
                max: 2.6e-11
                start: 1.33e-11
            setup:
                input_file: opal_input.in
                execution_type: serial


Providing an objective value
----------------------------
When using ``opal`` as the final code of an optimization run in rsopt you will need to provide an objective function in the
``options.objective_function`` field. The objective function is always executed in the same directory that ``opal``
was run in for each new job and so can easily be used to read any output from ``opal`` to perform required calculations.


.. [1] Adelmann, Andreas, et al. "OPAL a versatile tool for charged particle accelerator simulations."
       arXiv preprint arXiv:1905.06654 (2019).
.. [2] https://gitlab.psi.ch/OPAL/src/-/wikis/home