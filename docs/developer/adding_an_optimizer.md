# Adding a New Optimizer to rsopt

A development guide: what must be written, and what must be registered, to make a new optimization
package usable as `options.software: <name>` in an rsopt configuration file.

Written from code inspection and then revised against the actual work of adding Py-BOBYQA, which is the
worked example referenced throughout. Where the guide says "verified", the claim was checked by
running it rather than read off the source.

---

## 0. Decide the integration shape first

Everything downstream depends on this choice. There are three existing patterns:

| Pattern | Use when | Example | What you write |
| --- | --- | --- | --- |
| **A. Local optimizer via the shared generator** | The package is a serial, local optimizer that libEnsemble's `LocalOptInterfacer` **already supports** | `nlopt`, `scipy`, `dfols` | A `fields_to_pass` entry in `local_opt_generator.initialize_children` + a branch in `interface.get_local_optimizer_method`; **no** new generator, **no** new optimizer class (reuse `run.local_optimizer`). Not available for a package libEnsemble does not already know — see the warning below |
| **B. Standalone persistent generator** | The package drives its own optimization loop, or supports parallel/asynchronous batches of points | `pysot`, `dlib`, `mobo` (Xopt), `nsga2` (DEAP), `pybobyqa` | A new persistent generator + a new `libEnsembleOptimizer` subclass |
| **C. APOSMM sub-method** | The method is a local optimizer that APOSMM already knows how to call | `nlopt`/`scipy`/`dfols` under `aposmm` | Only `aposmm_support: True` plumbing and `format_user_specs` handling in `rsopt/libe_tools/optimizer_aposmm.py` |

Most new packages are **pattern B**; the rest of this guide assumes B and notes where A/C differ.

Questions to answer before writing code — each one maps to a concrete field later:

* Does it produce points **one at a time** or in **batches**? (→ how many points you push per `send`)
* Is it **asynchronous** (can absorb results as they trickle in) or **generational** (needs a full batch back
  before proposing again)? (→ choice of allocation function and its `user` flags)
* Does it expose an **ask/tell** interface, or does it **own the loop** and call your objective itself?
  (→ whether you need the child-process adapter in §1.2)
* **Single or multi-objective**? Constraints? (→ `sim_specs` outputs, `static_outputs` vs `dynamic_outputs`)
* Does it need an **initial design / start point** or a **restart history**? (→ `xstart`, `H0`, `load_start_sample`)
* Does it own its **own stopping rule**, or does libEnsemble stop it? (→ §1.3)
* What are its **hyperparameters**? (→ the `SoftwareOptions` model)
* Is it an **optional dependency**? (Answer is almost always yes → import it only inside the generator module.)

### Pattern A is only available for methods libEnsemble already supports

`local_opt_generator.py:9` imports `LocalOptInterfacer` from **libEnsemble's**
`libensemble.gen_funcs.aposmm_localopt_support`, not from rsopt. That class dispatches on a hardcoded
list of method names (`LN_*`, `scipy_*`, `dfols`, `pounders`, `blmvm`, `nm`, `ibcdfo_*`,
`external_localopt`) and raises `APOSMMException` for anything else. rsopt's own
`generator_functions/rsopt_localopt_support.py` is a stale fork that **nothing imports** — it is dead
code, and it contains an unfixed `NameError` (`localoptException` vs the defined `LocaloptException`).

So pattern A works only if the method is already in libEnsemble's list. For a new package you must
either upstream a `run_local_<package>` to libEnsemble, or revive rsopt's fork and re-point
`local_opt_generator.py` at it, or use pattern B. The same constraint applies to pattern C:
`persistent_aposmm` imports libEnsemble's support module directly, so `aposmm_support` cannot be
`True` for a package libEnsemble does not know.

Py-BOBYQA is serial and local in character, which makes pattern A look like the natural fit. It is
not available, and choosing it would have been actively harmful — see the `type: local` warning in §4.

---

## 1. Write the generator function

**File:** `rsopt/libe_tools/generator_functions/<package>.py`
**Reference implementations:** `persistent_dlib.py` (simplest), `persistent_pysot.py` (async with a
strategy object), `persistent_xopt_bo.py` (batched, multi-objective, constraints),
`persistent_deap_nsga2.py` (generational), `persistent_pybobyqa.py` (self-driving solver in a child
process, several concurrent instances).

Signature is fixed by libEnsemble:

```python
def persistent_<package>(H, persis_info, gen_specs, libE_info):
    ...
    return local_H, persis_info, FINISHED_PERSISTENT_GEN_TAG
```

Skeleton and the rules it has to obey:

```python
import numpy as np
from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG, EVAL_GEN_TAG
from libensemble.tools.persistent_support import PersistentSupport
import <package>            # optional dependency: imported here, never at rsopt import time


def persistent_<package>(H, persis_info, gen_specs, libE_info):
    persistent = PersistentSupport(libE_info, EVAL_GEN_TAG)
    local_H = np.zeros(len(H), dtype=H.dtype)

    # 1. unpack everything from gen_specs['user'] — this dict is built by the optimizer class in step 2
    lb, ub = gen_specs['user']['lb'], gen_specs['user']['ub']
    dim = gen_specs['user']['dim']

    # 2. instantiate the third-party optimizer

    # 3. push the first batch of points
    add_to_local_H(local_H, first_points)
    persistent.send(local_H[-n:][[i[0] for i in gen_specs['out']]])

    while True:
        tag, Work, calc_in = persistent.recv()
        if tag in [STOP_TAG, PERSIS_STOP]:
            break
        # 4. feed calc_in['f'] (etc.) back to the optimizer, keyed by calc_in['sim_id']
        # 5. ask for replacements and send them the same way

    return local_H, persis_info, FINISHED_PERSISTENT_GEN_TAG
```

### 1.1 Conventions and gotchas

* **`local_H` grows by `resize(..., refcheck=False)`.** Every existing generator has a private
  `add_to_local_H` helper that resizes, fills `x` (or `individual`), and assigns `sim_id` from a running
  counter. Copy that pattern; the fields you fill must match `gen_specs['out']`.
* **Only send the fields in `gen_specs['out']`** — `local_H[-n:][[i[0] for i in gen_specs['out']]]`.
* **Matching results back to proposals** is your job. `dlib` keeps a `{sim_id: request}` dict; `pysot`
  scans its proposal list for `record.sim_id`; `pybobyqa` keeps `{sim_id: instance_id}`. Whatever you
  do, `sim_id` has to be in `persis_in` (step 3) or it will not be in `calc_in`.
* **Results come back out of order and in partial batches.** Never assume the batch you receive
  corresponds to the batch you sent, or that it is complete.
* **rsopt always minimizes.** If the package maximizes, negate on the way in (`persistent_dlib` does
  `request.set(-row['f'])`).
* **Asynchronous generators must mark `given_back`** when they consume results
  (`local_H['given_back'][Work['libE_info']['H_rows']] = True`, see `persistent_xopt_bo.py`) — this
  pairs with the `only_persistent_gens` allocation flags set in step 2.
* **Never `import` the third-party package at rsopt module scope** and never import it from
  `rsopt/configuration/options/` — the whole lazy-dispatch design in `run.py` exists so that rsopt runs
  with none of the optional optimizers installed.
* **Absolute imports only** (project rule, see `CLAUDE.md`).

### 1.2 Self-driving solvers: the child-process adapter

Many derivative-free packages do not offer an ask/tell interface. They expose a single
`solve(objfun, x0, ...)` call that owns the loop and invokes `objfun(x)` whenever it wants a value.
That is incompatible with a generator that must return control to libEnsemble between points.

The established solution — libEnsemble's `LocalOptInterfacer` uses it, and `persistent_pybobyqa.py`
is a reduced version — is to **run the solver in a child process and block its objective callback**:

```python
def put_set_wait_get(x, comm_queue, parent_can_read, child_can_read):
    comm_queue.put(x)          # child asks for a point to be evaluated
    parent_can_read.set()
    child_can_read.wait()      # ... and blocks until the generator answers
    values = comm_queue.get()
    child_can_read.clear()

    assert np.allclose(x, values[0], rtol=1e-15, atol=1e-15), \
        'instance was given a result for a point it did not request'
    return values
```

Points worth copying:

* **Echo `x` back with `f` and assert they match.** The child can then verify it received the result
  for the point it actually asked for. With several instances in flight a mis-routed result would
  otherwise silently corrupt an interpolation model and produce a plausible but wrong answer. This
  assertion is what a mis-routing mutation trips first.
* **One instance keeps exactly one point in flight.** A self-driving solver cannot be made parallel.
  Parallelism instead comes from running **K independent instances**, each with its own child process
  and starting point, multiplexed onto the one shared history. Add an `instance` field to `gen_out`
  and write it in `add_to_local_H`, so a finished run can be decomposed into the searches that
  produced it.
* **Clean up deliberately.** Kill the child *and its descendants* (`psutil.Process(pid).children(recursive=True)`),
  then `join()` the process and `close()`/`join_thread()` the queue. A `multiprocessing.Queue` starts a
  feeder thread in the parent; if those leak, a long run accumulates them. Verify rather than assume:
  a 202-evaluation run with repeated instance relaunches was confirmed to start and end with the same
  thread count.
* **Wrap the child target** so an exception becomes a message on the queue (`ErrorMsg`) rather than a
  silent hang, and re-raise it in the parent.
* **Tear down in a `finally`**, so an exception mid-run does not leave orphaned processes.

### 1.3 The evaluation budget belongs to `sim_max`

`exit_criteria.sim_max` is the authority on how many simulations run, for every optimizer in rsopt,
and all concurrent instances or workers draw from that one budget together. If the third-party package
has its own budget parameter (`maxfun`, `max_evals`, ...), **determine what it actually does before
deciding how to set it**, because the two possibilities call for opposite treatment:

* If it is *only a stopping rule*, default it high enough that it never binds and let `sim_max` govern.
* If it *changes the search path* (step sizes, schedules, annealing), it must be derived from `sim_max`
  or the run will behave differently than the budget implies.

The test is cheap: run the package twice with two very different budgets and compare the first N
evaluated points. For Py-BOBYQA, `maxfun=150` and `maxfun=400` produced identical first-150 sequences,
proving it is purely a stopping rule; it is therefore defaulted to `1e6` and documented as
counterproductive to set, since an instance that exhausts it is restarted from scratch and loses its
model.

### 1.4 Non-finite objective values

Simulations fail, and rsopt hands the generator a penalty value when they do. Find out what the
package does with a non-finite objective before choosing a policy — the answers differ wildly. A
single `NaN` is instantly fatal to Py-BOBYQA (it terminates with `flag=-3` and a garbage `soln.f`),
while any large finite value is absorbed and the run converges normally. `pysot` cancels the record.

Where a substitution is right, use the same penalty rsopt already applies to failed jobs (`_PENALTY`
in `rsopt/simulation.py:15`, currently `1e9`), so a failed simulation and a `NaN` are treated alike.

> Note: `rsopt.simulation` cannot currently be imported as a first entry point — doing so raises
> `AttributeError: partially initialized module 'rsopt.configuration.schemas.code' has no attribute
> 'Code'` unless `rsopt.codes` is imported first. Until that circular import is fixed, a generator has
> to restate the constant with a comment pointing at the original rather than importing it.

---

## 2. Write the rsopt optimizer interface class

**File:** `rsopt/libe_tools/optimizer_<package>.py`
**Base:** `rsopt/libe_tools/optimizer.py::libEnsembleOptimizer` (`rsopt/libe_tools/optimizer.py:52`)

The base class already handles libE_specs, executors, sim_f, persis_info, and the run call. A pattern-B
subclass normally overrides exactly three methods (see `optimizer_pysot.py` — the canonical minimal case):

```python
<package>_gen_out = [('x', float, None), ]   # None = dimension filled in at run time


class <Package>Optimizer(optimizer.libEnsembleOptimizer):

    def _configure_optimizer(self):
        gen_out = [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in <package>_gen_out]
        user_keys = {'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds,
                     'dim': self._config.dimension,
                     **self._config.options.software_options.model_dump()}
        self.gen_specs.update({'gen_f': persistent_<package>,
                               'persis_in': self._config.options.method.persis_in + [n[0] for n in gen_out],
                               'out': gen_out,
                               'user': user_keys})

    def _configure_allocation(self):
        self.alloc_specs.update({'alloc_f': only_persistent_gens,
                                 'out': [('given_back', bool)],
                                 'user': {'async_return': True, 'active_recv_gen': True}})

    def _configure_specs(self):
        self.nworkers = self._config.options.nworkers      # base class hardcodes 2 for local optimizers
        super()._configure_specs()
```

Notes:

* `tools.set_dtype_dimension` (`rsopt/libe_tools/tools.py`) is what turns `('x', float, None)` into a
  correctly sized dtype; 2-tuples pass through untouched.
* **Allocation function choice encodes the sync/async question.** Asynchronous: `only_persistent_gens`
  with `{'async_return': True, 'active_recv_gen': True}` and `out=[('given_back', bool)]`
  (pysot/dlib/mobo/pybobyqa). Generational: `only_persistent_gens` with
  `{'give_all_with_same_priority': True}` (nsga2). Local/APOSMM-style: `persistent_aposmm_alloc`.
* **`nworkers`**: the base class fixes `self.nworkers = 2` (1 generator + 1 sim). Any parallel-capable
  generator must override `_configure_specs` to take `nworkers` from the config, and typically passes
  `nworkers - 1` into `user_keys` as the number of concurrent evaluations the generator should keep
  in flight (`dlib`: `'workers'`, `mobo`: `'processes'`, `pybobyqa`: `'instances'`).
* **This is where configuration-aware validation goes.** See §3.
* **Known inconsistency to avoid copying:** `optimizer_dlib.py` splices `**self._config.options.software_options`
  (a pydantic model) instead of `**...model_dump()`. Use `.model_dump()`. (`optimizer_aposmm.py` also
  still calls the deprecated pydantic v1 `.dict()`.)

---

## 3. Write the options schema

**File:** `rsopt/configuration/options/<package>.py`
**Base models:** `rsopt/configuration/schemas/options.py` (`SoftwareOptions`, `Method`, `Options`, `OptionsExit`)

Three models, mirroring `pybobyqa.py`/`mobo.py`:

```python
class <Package>Options(options.SoftwareOptions, extra='forbid'):
    # every user-tunable hyperparameter, with pydantic Field(description=...) — these descriptions are
    # the source material for the docs page in step 6
    some_setting: int = pydantic.Field(10, description='...')


class Method<Package>(options.Method):
    name: typing.Literal['<package>'] = '<package>'
    aposmm_support = False           # True only for pattern C
    local_support = False            # True only for pattern A
    persis_in = ['f', 'sim_id']      # what the generator needs back from the sim workers
    sim_specs = options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={},
    )
    option_spec = <Package>Options   # REQUIRED: how Options.validate_software_options finds this model


class <Package>(options.OptionsExit):
    software: typing.Literal['<package>'] = '<package>'
    method: typing.Union[Method<Package>] = pydantic.Field(Method<Package>(), discriminator='name')
    software_options: <Package>Options = pydantic.Field(default=<Package>Options())
```

Gotchas, several of which are live bugs elsewhere in the tree:

* **`option_spec` is not optional in practice.** `Options.validate_software_options`
  (`rsopt/configuration/schemas/options.py:95`) looks up `option_spec` on each method model to decide
  what to validate the user's `software_options` block against. `MethodPysot` omits it — don't copy that.
* **`name` must match the software key.** `MethodNsga2` declares `typing.Literal['pysot']` with default
  `'nsga2'` — a copy/paste bug. Get this right or the discriminator misbehaves.
* **Subclass `SoftwareOptions`.** `pysot`, `nsga2` and `mobo` subclass `pydantic.BaseModel` directly.
* **Set `extra='forbid'`** so a misspelled option is rejected instead of silently ignored.
* **Do not add a second `discriminator` on an already-`Annotated` field.** Commits `b31a259`/`5210f8b`
  removed exactly that; pydantic > 2.8.2 raises a fatal error for it.
* **Multi-objective / variable-width outputs** use `dynamic_outputs`: a mapping
  `{'<field on options or software_options>': ('<H field>', type)}`, resolved into a sized dtype by
  `Options.initialize_dynamic_outputs`. See `mobo.py` (`num_of_objectives` → `('f', float, n)`).
  Caveat: `SimSpecs._initialized_dynamic_outputs` is a `ClassVar` list that is *appended* to during
  validation, so it is shared across instances and accumulates on repeat validation — if the new
  optimizer needs dynamic outputs, expect to fix or work around this.
* **`software_options` with required fields** (like `mobo`) must not be given a default; optional ones
  get `= <Package>Options()`.
* Options models must stay import-light — no third-party optimizer imports here.

### Validation that the options model cannot do

An options model sees only its own fields. It has no access to the problem dimension, the bounds, the
parameter list, or `nworkers`. Any check that needs those **must** live in `_configure_optimizer`,
which still runs before libEnsemble starts a single worker, so it is just as fail-fast.

Split the work:

* **In the pydantic model** — types and shape only (`list[list[float]]`, positive ints, enums).
* **In `_configure_optimizer`** — anything relational: vector length against `self._config.dimension`,
  values against `self._config.lower_bounds` / `upper_bounds`, counts against a setting that may itself
  have been defaulted from `nworkers`.

Error messages from that second group should state **both** the expected value and what the user
supplied, and should say where a defaulted limit came from. When a limit is derived (`instances`
defaulting to `nworkers - 1`), a user who never set it has no way to guess the number otherwise:

```
additional_instance_starts entry 0 has 3 value(s), but this problem has dimension 2. Starting points
are given in the flattened parameter vector, so multi-dimensional parameters contribute more than one
value each.

additional_instance_starts lists 4 starting point(s), but at most 2 may be given: instance 0 always
starts from the `start` values of the parameters, leaving instances-1 = 2 to be set explicitly
(`instances` was not given, so it defaults to nworkers-1 = 3).
```

Note the dimension is the **flattened** parameter vector, not the number of named parameters: a
`RepeatedNumericParameter` (declared with `dimension: N`) contributes N entries. Say so in the message.

Be aware that rsopt does **not** currently validate `min <= start <= max` for parameters themselves, so
validating bounds on a new option is stricter than the surrounding code. That is the right direction,
but worth noting rather than assuming the check exists elsewhere.

---

## 4. Registry entries

Adding the optimizer means touching this fixed set of registration points:

1. **`rsopt/configuration/options/__init__.py`** — import the module and add
   `<package> = ('optimize', <package>.<Package>)` to `SUPPORTED_OPTIONS`
   (`rsopt/configuration/options/__init__.py:7`). This is what makes the name valid in a config file,
   via `get_optimize_names()` / `get_optimize_models()` used by `parse.py` and
   `rsopt/configuration/schemas/configuration.py`.
2. **`rsopt/run.py`** — add a lazily-importing factory function next to the others and register it in
   `run_modes` (`rsopt/run.py:177`). Keep the import inside the function body.
3. **`rsopt/package_data/optimizer_schema.yml`** — add a `<package>: {type: global|local, methods: {...}}`
   block. For a global optimizer the entry is currently informational, but every supported package has
   one and `libEnsembleOptimizer._OPT_SCHEMA` reads the file.

   > **Warning — do not use `type: local` for a package libEnsemble does not know.**
   > `run._local_opt_startup` writes every installed `type: local` package name into libEnsemble's
   > `.opt_modules.csv`, and `aposmm_localopt_support` validates that file against its own optimizer
   > list **at import time**. An unrecognized name there raises `APOSMMException` on
   > `import rsopt.libe_tools.optimizer`, which breaks *every* rsopt optimizer — but only for users who
   > actually have the new package installed, which makes it a nasty one to catch in review. Verified:
   >
   > ```
   > $ printf 'scipy,dfols,pybobyqa' > .../libensemble/gen_funcs/.opt_modules.csv
   > $ python -c "import rsopt.libe_tools.optimizer"
   > APOSMMException: APOSMM Error: unrecognized optimizers {'pybobyqa'}
   > ```
   >
   > After registering, confirm the file still contains only the names libEnsemble knows.
4. **`rsopt/pkcli/optimize.py`** — add the software name to the `_final_result` dispatch
   (`rsopt/pkcli/optimize.py:51`) so a best-result summary prints at the end, and update the docstring
   listing valid `software` values in `configuration()`.
5. **`pyproject.toml`** — add the package to the `full` extra with a comment naming the optimizer it
   serves. Do **not** add it to base `dependencies`.
6. (Pattern A/C only) **`rsopt/libe_tools/interface.py::get_local_optimizer_method`** and the
   `aposmm`/local-opt option models.

---

## 5. Examples

* **Example directory** — either `examples/<package>_example/` or, for a standard test problem,
  `examples/problems/<name>/` (as `zdt4` and `himmelblau` do). A Python objective plus a YAML config.
  Comment the config: an example is documentation, and the settings that are non-default are exactly
  the ones a reader needs explained.
* **`rsopt/package_data/example_registry.yml`** — register with a `files` list (config file **last**),
  the expected `result`, and `job_type: optimize`.

Two things about the registry are not obvious from reading it:

* **`rsopt/package_data/examples/` is a flat directory of tracked copies, not a symlink**, despite the
  constant pointing at it being named `EXAMPLE_SYMLINK`. Files listed in the registry are resolved
  against *that* directory, so **a new example must also be copied into it** or nothing can find it.
  Those copies have already drifted badly from `examples/`: as of this writing all four previously
  registered examples fail validation against the current pydantic models, so
  `tests/regression_tests/test_run_examples.py` cannot pass for any of them. Do not assume a green
  registry means anything until that is fixed.
* **Registry paths may be nested** (`problems/himmelblau/config_pybobyqa.yml`), but only because
  `copy_example_files` copies files out **by basename**. The destination has to be flattened; the
  original code used the registry path for both source and destination and raised `FileNotFoundError`
  on any nested entry. Configs reference their objective file as a bare name, so flat destinations are
  also what the configs expect.

**Before writing an exact `result` into the registry, confirm the run is deterministic.** Run it at
least three times and compare the minimum *and* the per-instance evaluation counts. An example built
for a regression test should avoid randomness deliberately — fixed starting points, global-restart
heuristics off — so that exact comparisons are legitimate. The Himmelblau example is bit-identical
across repeats for this reason.

---

## 6. Tests

Written for pytest and run from inside `tests/` (per `CLAUDE.md`).

### 6.1 A standalone harness for the generator

Test the generator **without libEnsemble in the loop** by substituting a fake for `PersistentSupport`
(monkeypatch the name in the generator module). This is where the concurrency and routing logic
actually gets exercised, and it runs in seconds.

The fake must be adversarial in the ways real workers are:

* assign `sim_id`s and evaluate points;
* return results **out of order**;
* return only **part** of what is outstanding, so points stay in flight across iterations;
* choose *which* outstanding points complete **fairly**.

That last point is not a detail. A first version returned the most recent outstanding points
(`reversed(outstanding)[:batch_limit]`), which is LIFO and starved the oldest point forever. One
instance produced 1 point while its peers produced 46, and two tests had been passing while only
exercising two of their three instances. Use a seeded permutation to pick which complete, then order
the returned batch newest-first so delivery is still out of order.

Worth covering: the minimum is found; the first point equals the start point; instances run
concurrently and the in-flight count is what you expect; partial batches keep points in flight;
a non-finite objective does not kill the run; a converged instance is relaunched; the run ends when
instances retire; child processes are cleaned up; the `instance` field is recorded.

### 6.2 An options/validation test

Build configurations in memory with `parse.parse_optimize_configuration({...})`, then call
`_configure_optimizer()` directly — no libEnsemble needed. Assert on the *content* of the error
messages, not just that something was raised: the message is the feature.

### 6.3 An end-to-end regression test

Drive the example **through the registry** rather than from `examples/`, so the registry wiring is
itself under test. Guard the optional dependency with `pytest.importorskip`.

The strongest assertion available for a deterministic optimizer is **sequence equivalence**: the points
rsopt evaluates should be identical, point for point, to the package driven directly. Build the
solver arguments from the `gen_specs` the optimizer actually produces rather than restating them, so
the test compares the configured run against itself and does not quietly go stale when a default
changes.

Two traps found while writing this test:

* **rsopt's `atexit` cleanup depends on the working directory.** `pkcli/optimize.configuration`
  registers `run.cleanup`, which resolves paths relatively at interpreter exit. A test that changes
  directory and changes back gets a `FileNotFoundError` traceback after the suite passes, and drops
  `H_*.npy` files wherever it happened to be. Re-register a `chdir` back into the run directory after
  calling `configuration()`; `atexit` is LIFO, so a later registration runs first.
* **`scaling_within_bounds` perturbs start points by an ulp.** When a solver rescales onto the unit
  cube and back, a value that is not exactly representable does not survive the round trip
  (`4.2` in `[-5, 5]` comes back as `4.199999999999999`). Do not assert exact equality between a
  configured start point and the first evaluated point; use a tight relative tolerance. Exact equality
  is still correct for sequence comparison, where both sides go through the same scaling.

### 6.4 Verify the tests, not just the code

* **If every test passes on the first run, mutate the code and check they fail.** Break one thing at a
  time — mis-route a result, remove the NaN guard, never relaunch, ignore user-supplied start points,
  introduce an off-by-one in a limit — and confirm the intended test catches each, then restore. This
  caught a genuine harness defect (§6.1) that had been hiding a starved instance, and it is the only
  way to know an assertion has teeth.
* **Establish a baseline before claiming no regressions.** `git stash push` only your own tracked
  files, run the suite, unstash, run again, and compare. rsopt's suite has a substantial number of
  pre-existing failures (missing `nlopt`, missing `pykern`, sirepo-dependent modules, and modules that
  no longer exist); without a baseline it is impossible to say whether a failure is yours.

---

## 7. Documentation

* **New page `docs/optimizers/<package>.rst`** — follow `docs/optimizers/dlib.rst`:
  label (`.. _<package>_ref:`), what the algorithm is + citation, whether it runs in parallel and how
  `nworkers` is interpreted, install instructions for the optional dependency, then
  *Configuration* → *Codes Blocks* / *Options* (every `software_options` key with type and
  required/optional) / *Objective Function* (shape of the return value) / *Example Options Block*.
  The page is picked up automatically by the `optimizers/*` glob toctree in `docs/commands.rst:100`.
* **`docs/commands.rst`** — add a bullet to the "Optimizer Software" list (from line 106) with a
  one-sentence description and a numbered footnote reference; add the matching footnote at the bottom.
* **`docs/options.rst`** — only if the new optimizer changes the meaning of a *global* option
  (e.g. a new interpretation of `nworkers` or `exit_criteria`).
* **`CLAUDE.md`** — update the `run_modes` software list in the "Optimizer/sampler dispatch" section.

> **`docs/.gitignore` line 1 is `*`.** Only `.gitignore`, `_static/`, `_templates/` and `index.rst` are
> unignored. Existing `.rst` files are tracked and behave normally, but a **new** page is invisible to
> `git add .` and will be silently left out of the commit. Add it with `git add -f`.

Two content rules worth following, both learned from the Py-BOBYQA page:

* **Document deviations from the package's own defaults as deviations**, with the reason. rsopt turns
  `seek_global_minimum` and `scaling_within_bounds` on although Py-BOBYQA defaults both off; a reader
  comparing the two sets of documentation needs to be told which is which.
* **Explain the relationship to the optimizers already available.** Adding a third BOBYQA-family
  solver is only useful if the page says when to choose it over `nlopt`'s `LN_BOBYQA` and over `dfols`.
* **Verify external links and cited defaults** rather than inferring them by analogy with a sibling
  package's documentation URLs.

---

## 8. Checklist

- [ ] Integration pattern chosen (A / B / C); pattern A/C availability confirmed against libEnsemble's list
- [ ] `rsopt/libe_tools/generator_functions/<package>.py`
- [ ] Budget semantics established empirically; `sim_max` left as the authority
- [ ] Non-finite objective policy established empirically
- [ ] `rsopt/libe_tools/optimizer_<package>.py`
- [ ] `rsopt/configuration/options/<package>.py` (`SoftwareOptions` + `Method` with `option_spec` + `Options`)
- [ ] Relational validation in `_configure_optimizer`, with expected-vs-supplied error messages
- [ ] `SUPPORTED_OPTIONS` entry
- [ ] `run.py` factory + `run_modes` entry
- [ ] `optimizer_schema.yml` entry; `.opt_modules.csv` confirmed unchanged
- [ ] `pkcli/optimize.py` `_final_result` + docstring
- [ ] `pyproject.toml` `full` extra
- [ ] Example directory, files copied into `rsopt/package_data/examples/`, `example_registry.yml` entry
- [ ] Determinism of the example confirmed over repeated runs before recording `result`
- [ ] Generator tests against a fair, out-of-order, partial-batch harness
- [ ] Options/validation tests asserting on message content
- [ ] End-to-end regression test driven through the registry, with sequence equivalence
- [ ] Tests mutation-checked; suite baseline compared
- [ ] `docs/optimizers/<package>.rst` (`git add -f`) + `docs/commands.rst` bullet & footnote + `CLAUDE.md`
- [ ] With the new package *uninstalled*, rsopt still imports and another optimizer still runs
