.. _opal_ref:

``OPAL``
===========

The particle accelerator tracking code ``OPAL`` [1]_ has special support in rsopt provided by the Sirepo library.
Using Sirepo, rsopt can parse ``OPAL`` input files, automatically replacing and updating values given
for parameters and settings with no additional work required by the user. An example setup is shown below::

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
The parameters are then used to vary the RFCAVITY `FINSS_RGUN`'s `LAG` value and SOLENOID `FIND1_MSOL10`'s strength.

In setup you only need to provide the input file name, there is a restriction on the parser that all OPAL input must be
within the given input file (the CALL command is not currently supported by the parser).
rsopt will handle reading and parsing both files during optimization or
parameter sweeps. If multiple workers can be used for the rsopt run then they will always work in separate directories for
each new job to prevent overwriting files.