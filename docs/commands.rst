Run Modes for rsopt
===================

Optimization
------------
To start an optimizer set up in a configuration file named ``my_config_file.yaml`` you can run::

    rsopt optimize configuration my_config_file.yaml

For a general walkthrough of  how to create your configuration file see the Configuration<configuration>
page. Here we will detail available optimizers and how to use them in the ``options`` section of your
configuration file.

An optimizer package is selected by the ``software`` setting in ``options``. Depending on
the package being used there may be many available algorithms or methods that are chosen through the ``method``
setting. Optional arguments may be passed to the optimizer as a dictionary given to ``software_options``.
As a quick example, here is how one could use the nlopt software package with the common Nelder-Mead algorithm::

    options:
        software: nlopt
        method: LN_NELDERMEAD
        software_options:
            ftol_abs: 1e-6
        objective_function: [obj_func.py, obj_f]

For a full list of software available in rsopt and details on methods and options see the
:ref:`Optimizer Software<opt_software>` section of this guide.

Specifying an Objective Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For each evaluation (be it a trial point from an optimizer or a point given to be sampled) rsopt will run the list
of jobs given in the ``codes`` section of the configuration. It is not generally expected that these programs are able
to return a final value needed for the optimizer so generally a Python function must be supplied that takes output
from the jobs and returns a value(s). Normally this function is supplied by the ``objective_function`` field in options
it is given as a list with the first entry the path to the Python file defining the function and the second entry the
name of a function defined in the Python file. Showing the previous example::

    options:
        software: nlopt
        method: LN_NELDERMEAD
        software_options:
            ftol_abs: 1e-6
        objective_function: [obj_func.py, obj_f]

Here the file ``obj_func.py`` would be assumed to be in the directory where rsopt is being run and the function ``obj_f``
is in the file ``obj_func.py``.

..
    NOTE: Will need to make changes here when multi-objective is added and when Switchyard is added (dict passing)
    TODO: Add links to examples that use objective functions

The job dictionary ``J`` will always be passed to the objective function (even if empty) so the functiontion should
always accept a single argument. If the previous job had ``setup.output_distribution`` specified the distribution
will be stored in the ``Switchyard`` which will be available from ``J``.
The return value should be a single ``float`` that will be passed to the optimizer.
So an example of a valid function would be:

.. code-block:: python
 :linenos:

    def obj_f(J):
        import numpy as np

        switchyard = J['switchyard']
        distribution = switchyard.species['species_0']
        enx = np.sqrt(np.average(distribution.x**2) * np.average(distribution.ux**2) - \
                      np.average(distribution.x * distribution.ux)**2)
        eny = np.sqrt(np.average(distribution.y**2) * np.average(distribution.uy**2) - \
                      np.average(distribution.y * distribution.uy)**2)

        obj = np.sqrt(enx**2 + eny**2)

        return obj

Here the job dictionary is not used. Instead it is assumed that one of the jobs that was run produced an output file
``my_sim_output.txt`` that contained some result of the simulation that could be read and processed by ``obj_f`` to
produce a value to be passed to the optimizer. Every time a set of jobs is run they will be stored in a common directory
to prevent data from being overwritten. The objective function will always be evaluated in the directory where the
set of jobs was just run so that there is easy access to any files written by your simulations.

In the special case where you may only be running a serial ``python`` job or your last job in the ``codes`` list is
a serial ``python`` job setting an ``objective_function`` is optional. You can just have the function set in your
``python`` job return a ``float`` and it will be directly passed to the optimizer if no ``objective_function`` was
provided.

**Note**: for *parallel* ``python`` jobs this is not the case. Parallel Python must be run in a subprocess
and no value can be directly returned. Therefore you must make sure to write any results to disk and
define an ``objective_function`` that can read them.



Optimizer Software
~~~~~~~~~~~~~~~~~~
.. _opt_software:

Valid entries for optimizers in ``software`` are given below. Some libraries may have different algorithms to choose from.
The algorithm used may be specified with the  ``method`` option. See below for a listing of supported algorithms in
each library.

``nlopt``: NLopt [1]_ is an open-source library of non-linear optimization algorithms. Currently, only a subset of algorithms
from NLopt are available in rsopt. For more detailed description of each algorithm please see the 'NLopt manual'_.
.. _NLopt manual: https://nlopt.readthedocs.io/en/latest/NLopt_Algorithms/
Method names are based upon NLopt's Python API naming scheme.

**Gradient-free methods** - these algorithms do not make use of the objective function gradient. The objective function
or setup.function, in the case of Python evaluation, should just return a single float that will be interpreted as
objective function value at the observation point.

    - ``LN_NELDERMEAD``: The well known Nelder-Mead method, sometimes just referred to as "simplex method".
    - ``LN_BOBYQA``: Bound Optimization BY Quadratic Approximation. A trust-region based method that uses a quadratic model of the objective.
    - ``LN_SBPLX``: A variant of Nelder-Mead that uses Nelder-Mead on a sequence of subspaces.
    - ``LN_COBYLA``: Constrained Optimization BY Linear Approximations. This is another trust-region method. COBYLA generally supports
      inequality and equality constraints, however, rsopt does not have an interface to pass constrains at this time.
    - ``LN_NEWUOA``: NEW Unconstrained Optimization Algorithm. NEWUOA performs unconstrained optimization using
      an iteratively constructed quadratic approximation for the objective function. Despite the name the NLopt manual
      notes that is generally better to use the even newer BOBYQA algorithm.

**Gradient-based methods** - these require passing gradient information for the objective function at the observation point.
For these methods the objective function or setup.function, in the case of Python evaluation, should return a tuple of
(f, fgrad) where f is the value of the objective function at the observation point x as a float and fgrad is the
gradient of f at x, fgrad should be an array of floats with the same dimension as x.

    - ``LD_MMA``: Method of Moving Asymptotes.

``scipy``: Several methods from the optimization module of the popular SciPy [2]_ library are available. For details
of the algorithms see the 'SciPy manual'_.
.. _SciPy manual: https://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html
Method names are based on SciPy's API naming scheme.

**Gradient-free methods** - these algorithms do not make use of the objective function gradient. The objective function
or setup.function, in the case of Python evaluation, should just return a single float that will be interpreted as
objective function value at the observation point.

    - ``Nelder-Mead``: The well known Nelder-Mead method, sometimes just referred to as "simplex method".
    - ``COBYLA``: Constrained Optimization BY Linear Approximations. This is another trust-region method. COBYLA generally supports
      inequality and equality constraints, however, rsopt does not have an interface to pass constrains at this time.

**Gradient-based methods** - these require passing gradient information for the objective function at the observation point.
For these methods the objective function or setup.function, in the case of Python evaluation, should return a tuple of
(f, fgrad) where f is the value of the objective function at the observation point x as a float and fgrad is the
gradient of f at x, fgrad should be an array of floats with the same dimension as x.

    - ``BFGS``: The Broyden-Fletcher-Goldfarb-Shanno algorithm. Can also be used like a gradient free method.
      If no gradient information is passed then BFGS will use a first-difference estimate.

``dfols``: The Derivative-Free Optimizer for Least-Squares (DFO-LS) [3]_ is an algorithm especially constructed to handle
objective functions formuated as least-squares problems.  Note that it is a single algorithm, and the ``method`` field
should also be set to ``dfols``. Note: you must supply the number of terms in the least-squares objective using
the field ``components`` under ``options``.

``aposmm``: The Asynchronously Parallel Optimization Solver for finding Multiple Minima (APOSMM) [4]_ is a global optimization
algorithm that coordinates concurrent local optimization runs in order to identify many local minima. APOSMM is included
in the libEnsemble library, for a description of its setup and options there see: https://libensemble.readthedocs.io/en/master/examples/aposmm.html.
However, rsopt automates much of the routine setup for APOSMM so a brief listing of relevant options is given below:

    - ``initial_sample_size``: Number of uniformly sampled points must be returned (non-nan value) before a local opt run is started.
    - ``max_active_runs``: Bound on number of runs APOSMM is advancing.
    - The optional values for ``gen_specs['user']`` may be passed to APOSMM through the ``software_options`` dictionary
      with the exception of ``sample_points`` which is not currently supported in the rsopt interface.

You must also supply a local optimization method that APOSMM will use with the ``method`` field.
The command must distinguish the local optimizer software and method in the form: ``software.method``
Currently just the NLopt
algorithms are available for use with APOSMM in rsopt. That is: ``LN_NELDERMEAD``, ``LN_BOBYQA``, ``LN_SBPLX``, ``LN_COBYLA``,
``LN_NEWUOA``, and ``LD_MMA``. To use LN_NELDERMEAD for example one should have ``method: nlopt.LN_NELDERMEAD``.

Parameter Scans
---------------

To start a parameter scan set up in a configuration file named ``my_config_file.yaml`` you can run::

    rsopt sample configuration my_config_file.yaml

For a general walkthrough of  how to create your configuration file see the Configuration<configuration>
page. Here we will detail available samplers availabe and how to use them in the ``options`` section of your
configuration file.

The sampler type is selected by the ``software`` setting in ``options``. The number of simultaneous
points to sample is chosen by the ``nworkers`` setting in ``options``. If you are running parallel
enabled simulations with N cores per simulation and M workers keep in mind you should have N*M cores available on
the machine(s) being used or you may see a significant increase in run time from expected (or possibly even errors).
As an example, to sample on a uniform mesh with 4 workers simultaneously running you would include in your configuration
file::

    options:
        software: mesh_scan
        nworkers: 4



Sampler Software
~~~~~~~~~~~~~~~~~~
.. _sampler_software:

Valid entries for samplers in ``software`` are given below. Please see the links for a description of the sampler and
any additional setup required.

- ``mesh_scan``: Samples a points on a uniform mesh. The mesh is either constructed from (min, max, samples), taking equally
  spaced `samples` between `min` and `max` or can be from a user defined mesh stored in NumPy's default `.npy` format.
  For N parameters and M `samples` this will result in the evaluation of N*M points in total.
- ``lhc_scan``: Samples points using a Latin Hypercube. The bounds are determined from `min` and `max` and an additional
  argument ``batch_size`` is required in options to give the number of points to run in the sample.
- ``start``: Can be used with `rsopt sample start` to run the configuration file on just the start point for each parameter.
  This is also useful as a method to help with debugging errors during simulation chains. It will ignore most other
  run configuration such as `nworkers` and `software`.

Miscellaneous
-------------
.. _misc_commands:

Other useful helper commands.

- ``pack``: Can be used to create a tarball including all local files needed to run the configuration file specified.
  Will include all simulation run files and Python scripts defined in the config file directory. If the included Python scripts
  have imports locally defined the import module files will also be included. Imports defined or installed elsewhere will
  not be included in the tarball.
  Full command is ``rsopt pack configuration config_name``.




.. [1] https://github.com/stevengj/nlopt
.. [2] https://www.scipy.org/
.. [3] https://github.com/numericalalgorithmsgroup/dfols
.. [4] https://doi.org/10.1007/s12532-017-0131-4
