.. _dfols_ref:

DFO-LS Optimization Methods
===========================

The Derivative-Free Optimizer for Least-Squares (DFO-LS) [1]_ is an algorithm especially constructed to handle
objective functions formuated as least-squares problems.

Methods
-------

- dfols: Though  it is a single algorithm the ``method`` field should also be set to ``dfols``. **The number of terms
  in the least-squares objective using the field ``components`` under ``options``.**

**For dfols the objective function or setup.function, in the case of Python evaluation, should return a tuple of
(f, fvec) where f is the value of the objective function at the observation point x as a float and fgrad is the
gradient of f at x, fgrad should be an array of floats with the same dimension as x.

.. [1] https://github.com/numericalalgorithmsgroup/dfols