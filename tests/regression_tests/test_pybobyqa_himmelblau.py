"""End-to-end regression test for the Py-BOBYQA optimizer.

Runs the packaged Himmelblau example through the full rsopt stack and checks both the result and
the route it took to get there. The example is deliberately free of randomness -- fixed starting
points, no global-restart heuristic -- so every evaluated point is reproducible, which lets the
run be compared against Py-BOBYQA driven directly.

Run from inside `tests/regression_tests/`.
"""
import atexit
import os
import shutil

import numpy as np
import pytest

from rsopt import EXAMPLE_SYMLINK, EXAMPLE_REGISTRY
from rsopt import parse
from rsopt.libe_tools.generator_functions.persistent_pybobyqa import _SOLVE_KEYS, DEFAULT_MAX_EVALS
from rsopt.libe_tools.optimizer_pybobyqa import PybobyqaOptimizer
from rsopt.pkcli.optimize import configuration

pybobyqa = pytest.importorskip('pybobyqa')

EXAMPLE_NAME = 'pybobyqa_himmelblau_example'
INSTANCES = 3

# The four global minima of Himmelblau's function, all with f = 0. The example starts a search in
# the basin of the first three; nothing starts in the basin of the fourth.
MINIMA = np.array([[3.000000, 2.000000],
                   [-2.805118, 3.131312],
                   [-3.779310, -3.283186],
                   [3.584428, -1.848126]])
UNREACHED_MINIMUM = 3


def nearest_minimum(x):
    return int(np.argmin(np.linalg.norm(MINIMA - np.asarray(x), axis=1)))


@pytest.fixture(scope='module')
def example():
    return parse.read_configuration_file(EXAMPLE_REGISTRY)['examples'][EXAMPLE_NAME]


@pytest.fixture(scope='module')
def run_example(example, tmp_path_factory):
    """Copy the registered example out and run it, yielding its history.

    Exercises the registry entry itself: the files are taken from the packaged examples directory
    by the paths the registry lists, which is the same route `rsopt quickstart` and the example
    regression test use.
    """
    work_dir = tmp_path_factory.mktemp('himmelblau')
    for source in example['files']:
        shutil.copyfile(os.path.join(EXAMPLE_SYMLINK, source),
                        work_dir / os.path.basename(source), follow_symlinks=True)

    config_filename = os.path.basename(example['files'][-1])
    original_dir = os.getcwd()
    os.chdir(work_dir)
    try:
        H, _, config = configuration(config_filename)
        # rsopt registers an atexit hook that copies logs using paths relative to the working
        # directory. atexit runs last in, first out, so registering here puts the process back in
        # the run directory before that hook fires.
        atexit.register(os.chdir, work_dir)
    finally:
        os.chdir(original_dir)

    return H, config


def instance_history(H, instance_id):
    """Points requested by one instance, in the order it requested them."""
    selected = H[H['instance'] == instance_id]
    return selected[np.argsort(selected['sim_id'])]


def test_registered_files_resolve(example):
    """Every path in the registry entry exists in the packaged examples directory."""
    for source in example['files']:
        assert os.path.isfile(os.path.join(EXAMPLE_SYMLINK, source)), \
            f'{source} is registered but not packaged'

    assert os.path.basename(example['files'][-1]).startswith('config_'), \
        'the configuration file must be last in the registry file list'


def test_result_matches_the_registry(run_example, example):
    H, _ = run_example

    assert np.isclose(H['f'].min(), example['result'], rtol=1e-9, atol=0.0), \
        f"registered result {example['result']!r} but the run produced {H['f'].min()!r}"


def test_every_instance_ran(run_example):
    H, _ = run_example

    assert set(H['instance']) == set(range(INSTANCES))
    counts = [int(np.sum(H['instance'] == i)) for i in range(INSTANCES)]
    assert min(counts) > 10, f'every instance should have done real work, got {counts}'


def test_instances_start_where_the_configuration_says(run_example):
    """Instance 0 starts from the parameter `start`, the rest from additional_instance_starts.

    Compared to a tight tolerance rather than exactly: the example sets `scaling_within_bounds`, so
    Py-BOBYQA maps each starting point onto the unit cube and back before evaluating it, which can
    move a value that is not exactly representable by one ulp (4.2 in [-5, 5] becomes
    4.199999999999999). The tolerance is still far tighter than any real difference in start point.
    """
    H, config = run_example
    given = config.options.software_options.additional_instance_starts

    assert np.allclose(instance_history(H, 0)['x'][0], config.start, rtol=1e-12, atol=0.0)
    for instance_id, start in enumerate(given, start=1):
        assert np.allclose(instance_history(H, instance_id)['x'][0], np.array(start),
                           rtol=1e-12, atol=0.0), \
            f'instance {instance_id} did not start at the point it was given'


def test_each_instance_converges_to_the_minimum_of_its_starting_basin(run_example):
    """Three distinct minima are found, and the basin nobody starts in is not."""
    H, _ = run_example

    found = []
    for instance_id in range(INSTANCES):
        points = instance_history(H, instance_id)
        best = points['x'][np.argmin(points['f'])]
        assert np.min(points['f']) < 1e-12, \
            f'instance {instance_id} did not converge, best f was {np.min(points["f"])}'
        found.append(nearest_minimum(best))

    assert len(set(found)) == INSTANCES, f'instances converged to duplicate minima: {found}'
    assert UNREACHED_MINIMUM not in found, \
        'no instance starts in the fourth basin, so that minimum must not be found'


def test_each_instance_matches_a_direct_pybobyqa_run(run_example):
    """The sequence of points rsopt evaluates is identical to Py-BOBYQA driven directly.

    The solver arguments are taken from the gen_specs the optimizer actually builds rather than
    restated here, so this compares the configured run against itself and stays honest if a
    default changes.
    """
    H, config = run_example

    optimizer = PybobyqaOptimizer(config)
    optimizer._configure_optimizer()
    user_specs = optimizer.gen_specs['user']

    solve_kwargs = {k: user_specs[k] for k in _SOLVE_KEYS if user_specs.get(k) is not None}
    solve_kwargs.setdefault('maxfun', DEFAULT_MAX_EVALS)
    bounds = (np.asarray(user_specs['lb'], dtype=float), np.asarray(user_specs['ub'], dtype=float))

    starts = [np.asarray(user_specs['xstart'], dtype=float)]
    starts += [np.asarray(s, dtype=float) for s in user_specs['additional_instance_starts']]

    def himmelblau(v):
        return float((v[0] ** 2 + v[1] - 11) ** 2 + (v[0] + v[1] ** 2 - 7) ** 2)

    for instance_id, x0 in enumerate(starts):
        direct = []

        def record(v):
            direct.append(np.array(v, copy=True))
            return himmelblau(v)

        pybobyqa.solve(record, x0, bounds=bounds, do_logging=False, **solve_kwargs)

        through_rsopt = instance_history(H, instance_id)['x']
        assert len(through_rsopt) == len(direct), \
            (f'instance {instance_id} evaluated {len(through_rsopt)} points, a direct run '
             f'evaluated {len(direct)}')
        assert np.array_equal(through_rsopt, np.array(direct)), \
            f'instance {instance_id} did not follow the same path as a direct Py-BOBYQA run'
