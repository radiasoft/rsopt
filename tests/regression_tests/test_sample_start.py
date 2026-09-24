"""End-to-end regression test for `rsopt sample start`.

`start` runs the chain only at the parameter `start` values, `n` times, whatever `software` the
configuration names. It must accept both sampler and optimizer configurations, and configurations
with no parameters at all. Each case writes a small Python-only configuration to a temporary
directory and runs it through the full rsopt/libEnsemble stack.

Run from inside `tests/regression_tests/`.
"""
import atexit
import os

import numpy as np
import pytest

from rsopt.pkcli import sample

OBJECTIVE = '''
def objective(x=0.0, y=0.0, offset=0.0):
    return x ** 2 + 10.0 * y + offset
'''

PARAMETERS = '''
      parameters:
        x:
          min: -3.
          max: 3.
          start: 0.5
          samples: 4
        y:
          min: -2.
          max: 2.
          start: -1.25
          samples: 3
'''

CODES = '''
codes:
  - python:
{parameters}
      settings:
        offset: 100.0
      setup:
        input_file: objective.py
        function: objective
        execution_type: serial
'''

SCAN_OPTIONS = '''
options:
  software: mesh_scan
  nworkers: 3
  software_options:
    sampler_repeats: 2
'''

OPTIMIZE_OPTIONS = '''
options:
  software: scipy
  method: Nelder-Mead
  nworkers: 3
  exit_criteria:
    sim_max: 50
'''

CASES = {
    'scan': (CODES.format(parameters=PARAMETERS) + SCAN_OPTIONS, [0.5, -1.25]),
    'optimize': (CODES.format(parameters=PARAMETERS) + OPTIMIZE_OPTIONS, [0.5, -1.25]),
    'no_parameters': (CODES.format(parameters='') + SCAN_OPTIONS, []),
}


def objective(x=0.0, y=0.0, offset=0.0):
    return x ** 2 + 10.0 * y + offset


def run_start(work_dir, config_text, n):
    (work_dir / 'objective.py').write_text(OBJECTIVE)
    (work_dir / 'config.yml').write_text(config_text)

    original_dir = os.getcwd()
    os.chdir(work_dir)
    try:
        H, _, config = sample.start('config.yml', n=n)
        # rsopt registers an atexit hook that saves the history using paths relative to the working
        # directory. atexit runs last in, first out, so registering here puts the process back in
        # the run directory before that hook fires.
        atexit.register(os.chdir, work_dir)
    finally:
        os.chdir(original_dir)

    return H, config


@pytest.mark.parametrize('n', [1, 3])
@pytest.mark.parametrize('case', CASES.keys())
def test_start_runs_the_start_point_n_times(case, n, tmp_path):
    config_text, expected_x = CASES[case]

    H, config = run_start(tmp_path, config_text, n)

    # Exactly n evaluations: `samples` and `sampler_repeats` in the configuration are ignored
    assert len(H) == n
    assert np.all(H['sim_ended'])
    assert np.array_equal(config.start, np.array(expected_x))

    expected_f = objective(*expected_x, offset=100.0)
    for row in H:
        assert np.array_equal(np.asarray(row['x'], dtype=float), np.array(expected_x))
        assert row['f'] == pytest.approx(expected_f)
