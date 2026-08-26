.. _pybobyqa_ref:

Py-BOBYQA Optimization Method
=============================

Py-BOBYQA [1]_ is a derivative-free trust-region solver for bound-constrained minimization of a
single objective. It builds a quadratic interpolation model of the objective from the points it has
already evaluated, which makes it well suited to expensive simulations and to objectives that are
noisy or only piecewise smooth. Unlike a plain local solver it also offers a *global* heuristic:
when a run converges it can restart from a new region while keeping what it has learned, so a single
Py-BOBYQA run can escape a local minimum.

rsopt already offers two related algorithms, so it is worth being clear about when to reach for this
one:

* ``nlopt`` with ``method: LN_BOBYQA`` is the original BOBYQA algorithm. It is a purely local solver
  and runs on a single worker.
* ``dfols`` is from the same authors as Py-BOBYQA but solves least-squares problems, and requires an
  objective that returns a vector of residuals.
* ``pybobyqa`` takes a single scalar objective like ``nlopt``, adds the global restart heuristic, and
  in rsopt runs several independent searches at once so that more than one worker can be kept busy.

Py-BOBYQA is not included in rsopt's base install requirements. It is installed with the ``full``
extra (``pip install rsopt[full]``) or directly with ``pip install Py-BOBYQA``.

How rsopt runs Py-BOBYQA
------------------------

Py-BOBYQA drives its own optimization loop and asks for one objective evaluation at a time, so a
single instance cannot keep more than one worker busy. To use the workers available, rsopt runs
several *instances* concurrently. Each instance is an independent Py-BOBYQA run with its own
starting point, trust region, and restart schedule, and all of them draw from the same evaluation
budget and write into the same history.

By default rsopt starts one instance per simulation worker, that is ``nworkers`` - 1, since one
worker is occupied running the generator itself. Every point in the history records which instance
requested it in an ``instance`` field, so a completed run can be broken back down into the
independent searches that produced it.

Because the instances are independent, the diversity of the result comes from where they start. See
`Starting points`_ below.

.. _pybobyqa_budget:

Evaluation budget
^^^^^^^^^^^^^^^^^

``exit_criteria.sim_max`` is the authority on how many simulations run, exactly as it is for every
other optimizer in rsopt. All instances draw from that one budget together, and the run stops as
soon as it is exhausted.

Py-BOBYQA has its own ``maxfun`` setting, but it is only a stopping rule for a single instance: it
does not change *which* points that instance evaluates, only when it gives up. rsopt therefore
leaves it effectively unset, so that termination is governed by ``sim_max`` alone. Setting ``maxfun``
low enough to bind is almost always counterproductive, because an instance that exhausts it is
restarted from scratch and loses the interpolation model it had built.

The run can also end before ``sim_max`` is reached. If ``restart_on_convergence`` is disabled, rsopt
stops once every instance has converged.

Configuration
-------------
Requirements and optional keys for setting up the configuration file to use Py-BOBYQA are given
below.

Codes Blocks
^^^^^^^^^^^^
No special configuration is needed in any portion of the :code:`codes` blocks to use Py-BOBYQA.

Options
^^^^^^^
The following required and optional keys can be used within the :code:`options:` block:

* :code:`software` *[str (required)]*: :code:`pybobyqa`
* :code:`software_options` *[dict (optional)]*: Settings for the solver and for how rsopt runs it.
  The available keys are listed below.

Keys controlling how rsopt runs the instances:

* :code:`instances` *[int (optional)]*: Number of independent Py-BOBYQA runs kept going at once.
  Defaults to ``nworkers`` - 1, so that every simulation worker has a search to feed.
* :code:`additional_instance_starts` *[list of lists (optional)]*: Explicit starting points for the
  instances after the first. See `Starting points`_. Defaults to no points given.
* :code:`restart_on_convergence` *[bool (optional)]*: When an instance converges, start a new run
  from a random point rather than letting that worker go idle. Set this to :code:`False` to have the
  run finish once every instance has converged. Defaults to :code:`True`.

Keys passed through to Py-BOBYQA. See [2]_ for full descriptions:

* :code:`seek_global_minimum` *[bool (optional)]*: Use Py-BOBYQA's multiple-restart heuristic to look
  for a global minimum. Requires bounds on all parameters, which rsopt always supplies. Defaults to
  :code:`True`, which differs from Py-BOBYQA's own default of :code:`False`; the heuristic is the
  main reason to choose this solver over the BOBYQA implementation in ``nlopt``.
* :code:`objfun_has_noise` *[bool (optional)]*: Tell Py-BOBYQA the objective is stochastic. This
  changes several internal defaults, including enabling restarts and using more interpolation
  points. Defaults to :code:`False`.
* :code:`scaling_within_bounds` *[bool (optional)]*: Let Py-BOBYQA rescale the parameters onto the
  unit cube internally, which helps when parameter ranges differ by orders of magnitude. Defaults to
  :code:`True`, which differs from Py-BOBYQA's own default of :code:`False`.
* :code:`npt` *[int (optional)]*: Number of interpolation points, which must satisfy
  :math:`n+1 \le npt \le (n+1)(n+2)/2` for a problem of dimension :math:`n`. Defaults to
  :math:`2n+1`, or to :math:`(n+1)(n+2)/2` when :code:`objfun_has_noise` is set.
* :code:`rhobeg` *[float (optional)]*: Initial trust region radius.
* :code:`rhoend` *[float (optional)]*: Trust region radius at which a run is taken to have converged.
  Defaults to :code:`1e-8`.
* :code:`maxfun` *[int (optional)]*: Evaluation budget for a single instance, counted across that
  instance's internal restarts. Not normally needed; see :ref:`Evaluation budget<pybobyqa_budget>`.
* :code:`user_params` *[dict (optional)]*: Advanced Py-BOBYQA settings passed through unchanged, for
  example :code:`{'restarts.use_restarts': True}`. See [3]_ for the available keys. These are
  validated by Py-BOBYQA rather than by rsopt.

.. _Starting points:

Starting points
^^^^^^^^^^^^^^^

Py-BOBYQA is deterministic in its starting point, so which minima a run finds is decided by where
its instances begin.

**Instance 0 always starts from the** :code:`start` **values given for the parameters** in the
:code:`codes` block. Points listed in :code:`additional_instance_starts` are used for instance 1
onwards, in the order they are given, and any instance not covered by the list starts from a point
drawn at random within the bounds. At most ``instances`` - 1 points may be given, since instance 0
is already accounted for.

A partial list is allowed. With four instances and one point given, instances 0 and 1 use the
configured points and instances 2 and 3 start randomly.

Each point is a list of values in the *flattened* parameter vector, so it must have one entry per
dimension of the problem. This is not the same as the number of named parameters when any of them
are multi-dimensional: a parameter declared with :code:`dimension: 3` contributes three entries. All
values must lie within the :code:`min` and :code:`max` of their parameter. rsopt reports the
expected and supplied lengths if they disagree, and validates every point before the run starts.

Starting points are used only when an instance first launches. When an instance converges and
``restart_on_convergence`` relaunches it, the new starting point is always random: restarting from
the same point would replay an identical sequence of evaluations and waste the budget.

Objective Function
^^^^^^^^^^^^^^^^^^
The objective function must return a single value of type :code:`float`. Minimization of the
objective is always assumed.

A non-finite objective value is fatal to Py-BOBYQA's interpolation model, so rsopt substitutes the
same large penalty value it applies to failed jobs if an evaluation returns ``NaN`` or an infinity.
The instance continues, treating the point as a very poor one.

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
  software: pybobyqa
  # 3 workers will run simulations. 1 worker will be running the Py-BOBYQA generator.
  # `instances` is not set, so 3 independent searches are started, one per simulation worker.
  nworkers: 4
  software_options:
    # Starting points for instances 1 and 2. Instance 0 uses the `start` values
    # of the parameters, so only `instances` - 1 = 2 points are given here.
    additional_instance_starts:
      - [-4.0, 4.0]
      - [-4.5, -4.5]
    # Let each instance restart itself to search for a global minimum
    seek_global_minimum: True
  exit_criteria:
    # All instances draw from this budget together
    sim_max: 200
  # objective_function can be optional if using python in codes
  objective_function: [objective.py, obj_f]


See ``examples/problems/himmelblau`` for a complete example. It runs three instances on Himmelblau's
function, which has four global minima, and places each starting point in a different basin so that
three of the four are found.

.. [1] https://github.com/numericalalgorithmsgroup/pybobyqa
.. [2] https://numericalalgorithmsgroup.github.io/pybobyqa/build/html/userguide.html
.. [3] https://numericalalgorithmsgroup.github.io/pybobyqa/build/html/advanced.html
