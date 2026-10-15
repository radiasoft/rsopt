"""Shared helpers for test_run_archive.py and test_log_tee.py.

Each test writes a small serial Python mesh_scan configuration into its own temporary directory (the working
directory during the test) and runs it in-process through rsopt and libEnsemble.
"""
import pathlib
from ruamel.yaml import YAML
from rsopt import parse
from rsopt import run

CONFIG_NAME = 'config.yml'
RUN_DIR_NAME = 'ensemble'
X_VALUES = [-1., 1.]

FUNCTION_SOURCE = '''
def quadratic(x, y):
    return x ** 2 + 10. * y


def objective(J):
    return J['inputs']['x'] ** 2 + 10. * J['inputs']['y']


def raises(J):
    raise RuntimeError('broken objective')
'''


def write_config(work_dir: pathlib.Path, objective: str = 'objective', **options) -> pathlib.Path:
    """Write the function file and a configuration file into work_dir. Returns the configuration file path."""
    (work_dir / 'function.py').write_text(FUNCTION_SOURCE)
    config = {
        'codes': [{'python': {
            'parameters': {'x': {'min': X_VALUES[0], 'max': X_VALUES[-1], 'start': 0., 'samples': len(X_VALUES)},
                           'y': {'min': 0.5, 'max': 0.5, 'start': 0.5}},
            'setup': {'input_file': 'function.py', 'function': 'quadratic', 'execution_type': 'serial'},
        }}],
        'options': {'software': 'mesh_scan', 'objective_function': ['function.py', objective], **options},
    }
    config_path = work_dir / CONFIG_NAME
    with open(config_path, 'w') as ff:
        YAML(typ='safe').dump(config, ff)
    return config_path


def parse_config(config_path: pathlib.Path):
    return parse.parse_sample_configuration(parse.read_configuration_file(config_path))


def start(work_dir: pathlib.Path, objective: str = 'objective', **options):
    """Write, parse, and run startup_sequence on a configuration. Returns (config, config_path)."""
    config_path = write_config(work_dir, objective=objective, **options)
    config = run.startup_sequence(parse_config(config_path), config_path)
    return config, config_path


def runner(config):
    return run.sample_modes[config.options.software](config)


def run_dir(work_dir: pathlib.Path) -> pathlib.Path:
    return (work_dir / RUN_DIR_NAME).resolve()
