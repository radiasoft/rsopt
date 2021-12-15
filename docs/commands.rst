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


.. _opt_software:

Optimizer Software
~~~~~~~~~~~~~~~~~~

.. toctree::
  :maxdepth: 1
  :glob:

  optimizers/*

Valid entries for optimizers in ``software`` are given below. Some libraries may have different algorithms to choose from.
The algorithm used may be specified with the  ``method`` option. See below for a listing of supported algorithms in
each library.

* :doc:`nlopt<optimizers/nlopt>`: NLopt [1]_ is an open-source library of non-linear optimization algorithms.

* :doc:`scipy<optimizers/scipy>`: Several methods from the optimization module of the popular SciPy [2]_ library are available. For details
  of the algorithms see the 'SciPy manual'_.
  .. _SciPy manual: https://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html

* :doc:`dfols<optimizers/dfols>`: The Derivative-Free Optimizer for Least-Squares (DFO-LS) [3]_ is an algorithm especially constructed to handle
  objective functions formuated as least-squares problems.

* :doc:`aposmm<optimizers/aposmm>`: The Asynchronously Parallel Optimization Solver for finding Multiple Minima (APOSMM) [4]_ is a global optimization
  algorithm that coordinates concurrent local optimization runs in order to identify many local minima.

* :doc:`pysot<optimizers/pysot>`: Python Surrogate Optimization Toolbox (pySOT) [5]_ implements a collection of surrogate optimization algorithms
  with several variations in surrogate model, optimization strategy, and experimental plan provided.

* :doc:`dlib<optimizers/dlib>`: Implements the global_function_search method from dlib [6]_.

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

.. toctree::
  :maxdepth: 1
  :glob:

  samplers/*

Valid entries for samplers in ``software`` are given below. Please see the links for a description of the sampler and
any additional setup required.

- :doc:`mesh_scan<samplers/mesh_scan>`: Samples a points on a uniform mesh. The mesh is either constructed from (min, max, samples), taking equally
  spaced `samples` between `min` and `max` or can be from a user defined mesh stored in NumPy's default `.npy` format.
- :doc:`lh_scan<samplers/lh_scan>`: Samples points using a Latin Hypercube.
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
.. [5] https://github.com/dme65/pySOT
.. [6] https://github.com/davisking/dlib
