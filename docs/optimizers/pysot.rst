.. _pysot_ref:

pySOT Optimization Methods
==========================

Python Surrogate Optimization Toolbox (pySOT) [1]_ implements a collection of surrogate optimization algorithms
with several variations in surrogate model, optimization strategy, and experimental plan provided.
pySOT includes support for asynchronous use of all optimization algorithms which is utilized by rsopt.

Currently rsopt implements a fixed choice for the three components and  uses:
``RBFInterpolant`` for the surrogate model, ``SRBFStrategy`` for the strategy, and ``SymmetricLatinHypercube`` for the
experimental plan.
The user can pass the following through ``software_options`` to configure pySOT:

- ``num_pts``: Sets the number of points that will be evaluated as part of the experimental planning phase before optimization begins. Defaults to 2 * (PARAMETER_DIMENSION + 1) if not set.

*The ``objective_function``or ``function`` in ``setup``, in the case of Python evaluation,
should just return a single float that will be interpreted as
objective function value at the observation point.*

Also supports use of arbitrary numbers of workers ``nworkers`` in ``options``.

.. [1] https://github.com/dme65/pySOT
