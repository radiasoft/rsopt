.. _genesis_ref:

``Genesis1.3``
===========

The FEL modeling code Genesis1.3 [1]_ can be parsed in rsopt through the lume-genesis library [2]_.
 rsopt can parse Genesis1.3 command files, automatically replacing and updating values given
for parameters with no additional work required by the user. An example setup is shown below::

    codes:
        - genesis:
            parameters:
                xrms:
                    min: 1e-5
                    max: 1e-4
                    start: 5e-5
                yrms:
                    min: 1e-5
                    max: 1e-4
                    start: 5e-5
            setup:
                input_file: genesis.in
                execution_type: parallel
                cores: 8



Distribution Piping
-------------------

When running a job with a sequence of codes output particle distributions from OPAL or elegant can be be automatically
piped to Genesis1.3 and used as a `distfile` input. In the settings section for the first code you must supply
the `output_distribution` parameter (keeping in mind possible :ref:`name mangling<elegant_name_mangling>`)
and then the `input_distribution` parameter in the Genesis setup block.
For example::

    codes:
        - elegant:
            setup:
                input_file: elegant.ele
                output_distribution: run_setup.output.sdds
                execution_type: parallel
                cores: 4
        - genesis:
            setup:
                input_file: tessa.in
                input_distribution: distribution.dist
                execution_type: parallel
                cores: 4



Providing an objective value
----------------------------
When using ``Genesis`` as the final code of an optimization run in rsopt you will need to provide an objective function in the
``options.objective_function`` field. The objective function is always executed in the same directory that ``genesis``
was run in for each new job and so can easily be used to read any output from ``genesis`` to perform required calculations.

.. [1] http://genesis.web.psi.ch/
.. [2] https://github.com/slaclab/lume-genesis