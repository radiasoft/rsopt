.. _dlib_ref:

dlib Optimization Method
========================

Implements the global_function_search method from dlib [1]_. For brevity this method  is simply referred  to as "dlib"
in this documentation and in rsopt.
This method is based on using the approximated
Lipschitz constant to define an upper bound on the search space that guides the optimization. This method is particularly
attractive because it requires no hyper parameter choices. For a very nice description of the method's operation see
here_.

The dlib algorithm works in parallel and supports use of arbitrary numbers of workers ``nworkers`` in ``options``.

The dlib library is not included as part of rsopt's install requirements. For information about installing
dlib for Python see `dlib's instructions`_.

Configuration
-------------
Requirements and optional keys for setting up the configuration file to use dlib are given below.

Codes Blocks
^^^^^^^^^^^^
No special configuration is needed in any portion of the :code:`codes` blocks to use dlib.

Options
^^^^^^^
The following required and optional keys can be used within the :code:`options:` block:

* :code:`software` *[str (required)]*: :code:`dlib`


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
  software: dlib
  # 9 workers will run simulations. 1 worker will be running pysot.
  nworkers: 10
  exit_criteria:
    sim_max: 400
  # objective_function can be optional if using python in codes
  objective_function: [objective.py, obj_f]


.. [1] https://github.com/davisking/dlib
.. _here: http://blog.dlib.net/2017/12/a-global-optimization-algorithm-worth.html
.. _dlib's instructions: https://github.com/davisking/dlib#compiling-dlib-python-api