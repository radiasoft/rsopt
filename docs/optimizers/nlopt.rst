.. _nlopt_ref:

NLopt Optimization Methods
==========================

NLopt [1]_ is an open-source library of non-linear optimization algorithms. Currently, only a subset of algorithms
from NLopt are available in rsopt. For more detailed description of each algorithm please see the 'NLopt manual'_.
.. _NLopt manual: https://nlopt.readthedocs.io/en/latest/NLopt_Algorithms/
Method names are based upon NLopt's Python API naming scheme.

Gradient-free methods
---------------------

These algorithms do not make use of the objective function gradient. *The ``objective_function``
or ``function`` in ``setup``, in the case of Python evaluation, should just return a single float that will be interpreted as
objective function value at the observation point.*

    - `LN_NELDERMEAD`: The well known Nelder-Mead method, sometimes just referred to as "simplex method".
    - `LN_BOBYQA`: Bound Optimization BY Quadratic Approximation. A trust-region based method that uses a quadratic model of the objective.
    - `LN_SBPLX`: A variant of Nelder-Mead that uses Nelder-Mead on a sequence of subspaces.
    - `LN_COBYLA`: Constrained Optimization BY Linear Approximations. This is another trust-region method. COBYLA generally supports
      inequality and equality constraints, however, rsopt does not have an interface to pass constrains at this time.
    - `LN_NEWUOA`: NEW Unconstrained Optimization Algorithm. NEWUOA performs unconstrained optimization using
      an iteratively constructed quadratic approximation for the objective function. Despite the name the NLopt manual
      notes that is generally better to use the even newer BOBYQA algorithm.

Gradient-based methods
----------------------

These require passing gradient information for the objective function at the observation point.
*For these methods The ``objective_function``or ``function`` in ``setup``, in the case of Python evaluation should return a tuple of
(f, fgrad) where f is the value of the objective function at the observation point x as a float and fgrad is the
gradient of f at x, fgrad should be an array of floats with the same dimension as x.*

    - ``LD_MMA``: Method of Moving Asymptotes.


.. [1] https://github.com/stevengj/nlopt