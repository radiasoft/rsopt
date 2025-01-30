import numpy as np
from rsopt import parse
from rsopt import run

@run.cleaup
def configuration(config: str):
    """Runs an optimization job.

    An optimization job will be started based on the content of the configuration file.
    The configuration file should have the software field in options set to one of:
      nlopt, dfols, scipy, aposmm, nsga2, pysot, dlib, mobo

    :param config: (str) Name of configuration file to use
    :return: None
    """
    _config_dict = parse.read_configuration_file(config)
    _config = parse.parse_optimize_configuration(_config_dict)
    _config = run.startup_sequence(_config)


    runner = run.run_modes[_config.options.software](_config)
    H, persis_info, _ = runner.run()

    if _config.is_manager:
        if _config.options.software in _final_result:
            _final_result[_config.options.software](H)

    return H, persis_info, _config


def _final_local_result(H):
    """Returns just one 'best' result"""
    best, index = np.nanmin(H['f']), np.argmin(H['f'])
    print("Minimum result:", H['x'][index], best)


def _final_global_result(H):
    """Looks at points declaired local minima. For cases where multiple 'best' results may be found."""
    print("Local Minima Found: ('x', 'f')")
    for lm in H[H['local_min']]:
        print(lm['x'], lm['f'])


_final_result = {
    'nlopt': _final_local_result,
    'aposmm': _final_global_result,
    'pysot': _final_local_result,
    'dlib': _final_local_result
}