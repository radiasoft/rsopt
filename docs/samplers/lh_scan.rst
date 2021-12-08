.. _lh_scan_ref:

Latin Hypercube Sampling
========================

Samples points using a Latin Hypercube. The bounds are determined from `min` and `max` of each parameter.

For a mesh scan if the final code of the job chain is serial Python and if an objective function is not provided (see below)
then the return value of the Python function must be either :code:`None` or :code:`float`. If the final code
of the job chain is serial Python and the function returns a :code:`float` the value will be recorded in the :code:`f`
field of the history file.

Configuration
-------------
Requirements and optional keys for setting up the configuration file to use Latin Hypercube Sampling are given below.

Codes Blocks
^^^^^^^^^^^
No special configuration is needed in any portion of the :code:`codes` blocks to use Latin Hypercube Sampling.

Options
^^^^^^^
The following required and optional keys can be used within the :code:`options:` block:

* :code:`software` *[str (required)]*: :code:`lh_scan`
* :code:`batch_size` *[int (required)]*: The number of sample points to evaluate.
* :code:`seed` *[int or None or str (optional)]*: Sets the seed to initialize the pseudo-random number generator used by the sampler.
  Behavior depends on the setting:
   * :code:`''`: **default** If an empty string is given, or seed is not explicitly included then a fixed seed is set.
     Repeated runs with this setting will always evaluate the same point.
   * :code:`None`: If seed is set to :code: `None` then a random seed will be used. **IMPORTANT**: To set a field to be
     :code:`None`-type in YAML the field must be empty. So the options block should look like:

    .. code-block:: yaml

     options:
      software: lh_scan
      seed:
      batch_size: 42


   * :code:`int`: If set  be any integer between 0 and 2**32 - 1 inclusive then the integer is used as the seed initialize the pseudo-random number generator.

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
