.. _mesh_scan_ref:

Mesh Scan
=========

Samples a points on a uniform mesh, or from a user defined set of values.
The mesh is either constructed from (min, max, samples), taking equally
spaced `samples` between `min` and `max` or can be from a user defined mesh stored in NumPy's default `.npy` format.
For N parameters and M `samples` this will result in the evaluation of N*M points in total.

For a mesh scan if the final code of the job chain is serial Python and if an objective function is not provided (see below)
then the return value of the Python function must be either :code:`None` or :code:`float`.

Configuration
-------------
Requirements and optional keys for setting up the configuration file to use Mesh Scan are given below.

Codes Blocks
^^^^^^^^^^^
* :code:`samples` *[int (required)]*: Each parameter must have a specified number of samples given.
  If :code:`samples: 1` then the parameter is set to its :code:`start` value.

Options
^^^^^^^
The following required and optional keys can be used within the :code:`options:` block:

* :code:`software` *[str (required)]*: :code:`mesh_scan`
* :code:`mesh_file` *[str (optional)]*: The name of a file giving the points to evaluate for the scan. The array should
  be formatted to have a shape of (N, M) where N is the length of the parameter vector and M is the number of samples.


Objective Function
^^^^^^^^^^^^^^^^^^
An objective function is not required for a sampling run, but may be provided. If an objective function is provided
the returned value will be recorded in the :code:`f` field of the history file.
The objective function must return a single value of type :code:`float`.

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
