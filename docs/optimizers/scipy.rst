.. _scipy_ref:

SciPy Optimization Methods
==========================

Several methods from the optimization module of the popular SciPy [1]_ library are available. For details
of the algorithms see the 'SciPy manual'_.
.. _SciPy manual: https://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html
Method names are based on SciPy API's naming scheme.

Gradient-free methods
---------------------

These algorithms do not make use of the objective function gradient. **The objective function
or setup.function, in the case of Python evaluation, should just return a single float that will be interpreted as
objective function value at the observation point.**

    - `Nelder-Mead`: The well known Nelder-Mead method, sometimes just referred to as "simplex method".
    - `COBYLA`: Constrained Optimization BY Linear Approximations. This is another trust-region method. COBYLA generally supports
      inequality and equality constraints, however, rsopt does not have an interface to pass constrains at this time.

Gradient-based methods
----------------------

These require passing gradient information for the objective function at the observation point.
**For these methods the objective function or setup.function, in the case of Python evaluation, should return a tuple of
(f, fgrad) where f is the value of the objective function at the observation point x as a float and fgrad is the
gradient of f at x, fgrad should be an array of floats with the same dimension as x.**

    - ``BFGS``: The Broyden-Fletcher-Goldfarb-Shanno algorithm. Can also be used like a gradient free method.
      If no gradient information is passed then BFGS will use a first-difference estimate.

.. [1] https://www.scipy.org/