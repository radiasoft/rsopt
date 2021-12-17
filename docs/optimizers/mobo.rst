.. _mobo_ref:

Multi-Objective Bayesian Optimization Methods
=============================================
Multi-Objective Bayesian Optimization (MOBO) implemented from the Xopt package [1]_ for details see also [2]_.
This algorithm attempts to determine the Pareto front of a multi-objective
problem using multi-objective Bayesian optimization. The acquisition function is
the expected hypervolume improvement (EHVI), implemented in botorch [3]_. Allows for
the specification of unknown constraints and proximal biasing  (From the mobo function docstring).

By default Xopt is not installed in the basic installation of rsopt.
Some examples for MOBO also require the library pymoo which is not installed with rsopt either.

Configuration
-------------
Requirements and optional keys for setting up the configuration file to use DFO-LS are given below.

Codes Blocks
^^^^^^^^^^^^
No special configuration is needed in any portion of the :code:`codes` blocks to use MOBO.

Options
^^^^^^^
The following required and optional keys can be used within the :code:`options:` block:

* :code:`software` *[str (required)]*: :code:`mobo`
* :code:`objectives` *[int (required)]*: Number of objectives returned by the evaluation function.
* :code:`constraints` *[int (required)]*: Number of constraints returned by the evaluation function.
* :code:`reference` *[list (required)]*: Reference point used for hypervolume calculation in the objective space
  should have the same dimensionality as objectives.
* :code:`software_options` *[dict (optional)]*: There are a number of significant options passed through :code:`software_options`
  as well for this optimizer:
    * :code:`fixed_cost` *[bool (optional)]*: Use fixed cost for each evaluation. This equates to the simulation budget being
      equivalent to the value set in `exit_criteria: sim_max`.
    * :code:`min_calc_to_remodel` *[int (optional)]*: Wait until at least :code:`min_calc_to_remodel` simulation evaluations have
      been returned before the model is trained. When :code:`min_calc_to_remodel` = :code:`nworkers` - 1 this equates
      to completely synchronous evaluation. If the simulation run time is much shorter than the model training time
      you may see much better performance by setting :code:`min_calc_to_remodel` > 1.
    * :code:`generator_options` *[dict (optional)]*: Dictionary passed directly to the mobo generator.
      * :code:`use_gpu` *[bool (optional)]*: Use available GPUs for model training.
    * :code:`constraints` *[dict (optional)]*: This must be included if the objective function also returns constraint
      values. Should be a dict where each value is a list specifying the inequality condition either
      `GREATER_THAN` or `LESS_THAN`. Names of the dict keys
      do not matter, **but the ordering of the dict must match the return order of the constraints in the objective**.
        .. code-block:: yaml

         options:
           constraints:
             c1: ['GREATER_THAN', 5.0]
             c2: ['LESS_THAN', 0.0]


Objective Function
^^^^^^^^^^^^^^^^^^
The objective function must return a tuple of type :code:`(objectives, constraints)` where both :code:`objectives`
and :code:`constraints` are 1D vectors (tuples, lists or NumPy arrays should all be valid).
Be careful to make sure the ordering of values returned by :code:`constraints`
matches that given in :code:`options: software_options: constraints`.

Example snippets (Using tuples to form the vectors):

.. code-block:: python
 :linenos:

    def my_function(x1, x2):
       # Definition of the TNK benchmark function
       objectives = (x1, x2)
       # See example options block before for additional required constraint configuration
       constraints = (x1 ** 2 + x2 ** 2 - 1.0 - 0.1 * np.cos(16 * np.arctan2(x1, x2)),
                      (x1 - 0.5) ** 2 + (x2 - 0.5) ** 2)

       return objectives, constraints



Example Options Block
^^^^^^^^^^^^^^^^^^^^^


.. code-block:: yaml

 options:
  nworkers: 4
  software: mobo
  objectives: 2
  constraints: 2
  reference: [1.4, 1.4]
  software_options:
    fixed_cost: True
    min_calc_to_remodel: 3  # min_calc_to_remodel == nworkers - 1 so this will be synchronous update
    use_gpu: False
    constraints:
      # Match with constraint values returned by above objective function
      c1: ['GREATER_THAN', 0]
      c2: ['LESS_THAN', 0.5]
  exit_criteria:
    sim_max: 80

See rsopt/examples/mobo_example for an example using MOBO.

.. [1] https://github.com/ChristopherMayes/xopt
.. [2] https://journals.aps.org/prab/abstract/10.1103/PhysRevAccelBeams.24.062801
.. [3] https://botorch.org/tutorials/multi_objective_bo
