.. _pysot_ref:

pySOT Optimization Methods
==========================


Python Surrogate Optimization Toolbox (pySOT) [1]_ implements a collection of surrogate optimization algorithms
with several variations in surrogate model, optimization strategy, and experimental plan provided.
pySOT includes support for asynchronous use of all optimization algorithms which is utilized by rsopt.

Currently rsopt implements a fixed choice for the three components and uses:
``RBFInterpolant`` for the surrogate model, ``SRBFStrategy`` for the strategy, and ``SymmetricLatinHypercube`` for the
experimental plan.

pySOT is not included in rsopt's basic install. It can installed via pip with:
   .. code-block:: bash

      pip install pySOT

Configuration
-------------
Requirements and optional keys for setting up the configuration file to use pySOT are given below.

Codes Blocks
^^^^^^^^^^^^
No special configuration is needed in any portion of the :code:`codes` blocks to use pySOT.

Options
^^^^^^^
The following required and optional keys can be used within the :code:`options:` block:

* :code:`software` *[str (required)]*: :code:`pysot`
* :code:`software_options` *[dict (optional)]*:
    * :code:`num_pts` *[int (optional)]*: Sets the number of points that will be evaluated as part of the
      experimental planning phase before optimization begins.
      Defaults to :math:`2 * (DIM + 1)` if not set.

Objective Function
^^^^^^^^^^^^^^^^^^
The objective function must return a single value of type :code:`float`. Minimization of the objective is always assumed.

.. code-block:: python
 :linenos:

    # As passed to options.objective_function:
    def obj_f(J):
        # Objective function is always passed
        # to the rsopt job dictionary `J`

        # ... Code to calculate objective value `f`

        return f

    # Example if using code block type `python`
    # without options.objective_function:
    def my_function(x, y):
        # Assuming user defined `parameters` (x, y)
        # in the configuration file

        f = x**2 + y**2 + x * y

        return f



Example Options Block
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

 options:
  software: pysot
  # 9 workers will run simulations. 1 worker will be running pysot.
  nworkers: 10
  software_options:
    num_pts: 42
  exit_criteria:
    sim_max: 400
  # objective_function can be optional if using python in codes
  objective_function: [objective.py, obj_f]



.. [1] https://github.com/dme65/pySOT
