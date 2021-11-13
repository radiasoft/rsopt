.. _aposmm_ref:

APOSMM Optimization Methods
===========================

The Asynchronously Parallel Optimization Solver for finding Multiple Minima (APOSMM) [1]_ is a global optimization
algorithm that coordinates concurrent local optimization runs in order to identify many local minima. APOSMM is included
in the libEnsemble library, for a description of its setup and options there see: https://libensemble.readthedocs.io/en/master/examples/aposmm.html.
However, rsopt automates much of the routine setup for APOSMM so a brief listing of relevant options is given below:

    - ``initial_sample_size`` (required): Number of uniformly sampled points must be returned (non-nan value) before a local opt run is started.
    - ``max_active_runs`` (optional): Bound on number of runs APOSMM is advancing.
    - The optional values for ``gen_specs['user']`` may be passed to APOSMM through the ``software_options`` dictionary
      with the exception of ``sample_points`` which is not currently supported in the rsopt interface.

You must also supply a local optimization method that APOSMM will use with the ``method`` field.
The command must distinguish the local optimizer software and method in the form: ``software.method``
Currently just the NLopt algorithms are available for use with APOSMM in rsopt.
That is: ``LN_NELDERMEAD``, ``LN_BOBYQA``, ``LN_SBPLX``, ``LN_COBYLA``,
``LN_NEWUOA``, and ``LD_MMA``. To use LN_NELDERMEAD for example one should have ``method: nlopt.LN_NELDERMEAD``.

**See NLopt<nlopt> for details on the return value requirements for the chosen method**

.. [1] https://doi.org/10.1007/s12532-017-0131-4