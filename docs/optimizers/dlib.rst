.. _dlib_ref:

dlib Optimization Methods
=========================

Implements the global_function_search method from dlib [6]_. This method is based on using the approximated
 Lipschitz constant to define an upper bound on the search space that guides the optimization. This method is particularly
attractive because it requires no hyper parameter choices. For a very nice description of the method's operation see
here_. Supports use of arbitrary numbers of workers ``nworkers`` in ``options``.

*The ``objective_function``or ``function`` in ``setup``, in the case of Python evaluation,
should just return a single float that will be interpreted as
objective function value at the observation point.*

.. [6] https://github.com/davisking/dlib
.. _here http://blog.dlib.net/2017/12/a-global-optimization-algorithm-worth.html