.. _nlopt_ref:

NLopt Optimization Methods
==========================

NLopt [1]_ is an open-source library of non-linear optimization algorithms. Currently, only a subset of algorithms
from NLopt are available in rsopt. For more detailed description of each algorithm please see the 'NLopt manual'_.
.. _NLopt manual: https://nlopt.readthedocs.io/en/latest/NLopt_Algorithms/
Method names are based upon NLopt's Python API naming scheme.

Configuration
-------------
Requirements and optional keys for setting up the configuration file to use NLopt are given below.

Codes Blocks
^^^^^^^^^^^^
No special configuration is needed in any portion of the :code:`codes` blocks to use NLopt.

Options
^^^^^^^
The following required and optional keys can be used within the :code:`options:` block:

* :code:`software` *[str (required)]*: :code:`nlopt`
* :code:`method` *[str (required)]*: Choose from methods in :ref:`methods Software<nlopt_methods>`
* :code:`software_options` *[dict (optional)]*: Pass options directly to the :code:`nlopt.opt` instance.
  Not all parameters or methods are available. All stopping parameters [2]_ are supported. Currently nonlinear constraints are not supported.

.. _nlopt_methods:

Available NLopt methods
-----------------------
The selection of local optimization methods in NLopt made available through rsopt are list below. Methods are classified
as either gradient-free or gradient-based.

Gradient-free methods
^^^^^^^^^^^^^^^^^^^^^

* :code:`LN_NELDERMEAD`: The well known Nelder-Mead method, sometimes just referred to as "simplex method".
* :code:`LN_BOBYQA`: Bound Optimization BY Quadratic Approximation. A trust-region based method that uses a quadratic model of the objective.
* :code:`LN_SBPLX`: A variant of Nelder-Mead that uses Nelder-Mead on a sequence of subspaces.
* :code:`LN_COBYLA`: Constrained Optimization BY Linear Approximations. This is another trust-region method. COBYLA generally supports
  inequality and equality constraints, however, rsopt does not have an interface to pass constrains at this time.
* :code:`LN_NEWUOA`: NEW Unconstrained Optimization Algorithm. NEWUOA performs unconstrained optimization using
  an iteratively constructed quadratic approximation for the objective function. Despite the name the NLopt manual
  notes that is generally better to use the even newer BOBYQA algorithm.

Objective Function
""""""""""""""""""
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

Gradient-based methods
^^^^^^^^^^^^^^^^^^^^^^

* ``LD_MMA``: Method of Moving Asymptotes.

Objective Function
""""""""""""""""""
The objective function must return a tuple of type :code:`(float, iter[floats])` where the first time is the evaluation of the
objective function :math:`f(\vec{x})` and the second term is the vector of the gradient :math:`\nabla f(\vec{x})`.
Minimization of the objective is always assumed.

.. code-block:: python
 :linenos:

    # As passed to options.objective_function:
    def obj_f(J):
        # Objective function is always passed
        # to the rsopt job dictionary `J`

        # ... Code to calculate objective value `f`

        return f, [dfdx, dfdy]

    # Example if using code block type `python`
    # without options.objective_function:
    def my_function(x, y):
        # Assuming user defined `parameters` (x, y)
        # in the configuration file

        f = x**2 + y**2 + x * y
        grad = [2*x + y, 2*y + x]

        return f, grad


Example Options Block
^^^^^^^^^^^^^^^^^^^^^


.. code-block:: yaml

 options:
  software: nlopt
  method: LN_BOBYQA
  # Run until tolerance is reached or exit_criteria is hit
  software_options: {'xtol_abs': 1e-6,
                     'ftol_abs': 1e-6}
  exit_criteria:
    # If model.rel_tol isn't reached after 400 simulations then rsopt will terminate
    sim_max: 30
  # objective_function can be optional if using python in codes
  objective_function: [objective.py, obj_f]

See rsopt/examples/quickstart_example for an example using NLopt.

.. [1] https://github.com/stevengj/nlopt
.. [2] https://nlopt.readthedocs.io/en/latest/NLopt_Python_Reference/#stopping-criteria
