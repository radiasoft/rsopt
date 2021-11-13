.. _dfols_ref:

DFO-LS Optimization Methods
===========================

The Derivative-Free Optimizer for Least-Squares (DFO-LS) [1]_ is an algorithm especially constructed to handle
objective functions formuated as least-squares problems.

Configuration
-------------
Requirements and optional keys for setting up the configuration file to use DFO-LS are given below.

Codes Blocks
^^^^^^^^^^^
No special configuration is needed in any portion of the :code:`codes` blocks to use DFO-LS.

Options
^^^^^^^
The following required and optional keys can be used within the :code:`options:` block:

* :code:`software` *[str (required)]*: :code:`dfols`
* :code:`method` *[str (required)]*: :code:`dfols`
* :code:`components` *[int (required)]*: Number of residuals in the objective function (see also objective function setup).
* :code:`software_options` *[dict (optional)]*: Pass options directly to the :code:`user_params` dictionary in the :code:`dfols` instance. See [2]_ for a list of available options.

Objective Function
^^^^^^^^^^^^^^^^^^
The objective function must return a tuple of type :code:`(float, iter[floats])` where the first term is the sum of
residuals :math:`\sum_i^n{r_i(x)^2}` and the iterable contains a vector of the residuals :math:`(r_i(x), ..., r_n(x))`.

Example snippets (Using NumPy to form the residual vectors):

.. code-block:: python
 :linenos:

    import numpy as np
    # As passed to options.objective_function:
    def obj_f(J):
        # Objective function is always passed
        # to the rsopt job dictionary `J`

        # ... Code to calculate `residuals`

        r = np.array(residuals)
        r_sum = np.sum(r**2)

        return r_sum, r

    # Example if using code block type `python`
    # without options.objective_function:
    def my_function(x, y):
        # Assuming user defined `parameters` (x, y)
        # in the configuration file

        x0, y0 = 5, 5

        r = np.array([x - x0, y - y0])
        r_sum = np.sum(r**2)

        return r_sum, r



Example Options Block
^^^^^^^^^^^^^^^^^^^^^


.. code-block:: yaml

 options:
  software: dfols
  method: dfols
  components: 214
  # Run until tolerance is reached or exit_criteria is hit
  software_options: {'user_params': {'model.rel_tol': 1e-4}}
  exit_criteria:
    # If model.rel_tol isn't reached after 400 simulations then rsopt will terminate
    sim_max: 400
  objective_function: [objective.py, obj_f]


See rsopt/examples/python_chwirut_example for an example using DFO-LS

.. [1] https://github.com/numericalalgorithmsgroup/dfols
.. [2] https://numericalalgorithmsgroup.github.io/dfols/build/html/advanced.html