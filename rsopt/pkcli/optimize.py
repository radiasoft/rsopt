import numpy as np
from rsopt import run
from rsopt import util


def configuration(config):
    _config = run.startup_sequence(config)

    software = _config.options.NAME
    try:
        nworkers = _config.options.nworkers
    except AttributeError:
        # Any method that doesn't allow user specification must use 2 workers
        nworkers = 2

    runner = run.run_modes[software](_config)
    H, persis_info, _ = runner.run()

    if _config.is_manager:
        util.save_final_history(config, _config, H, persis_info, nworkers, message='Run completed')
        if software in _final_result:
            _final_result[software](H)


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