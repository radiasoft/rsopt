import rsopt.parse as parse
import numpy as np
import os
from rsopt import run
from libensemble.tools import save_libE_output


def configuration(config):
    config_yaml = parse.read_configuration_file(config)
    _config = parse.parse_yaml_configuration(config_yaml)

    software = _config.options.NAME
    nworkers = _config.options.nworkers

    runner = run.run_modes[software](_config)
    H, persis_info, _ = runner.run()

    filename = os.path.splitext(config)[0]
    history_file_name = "H_" + filename + ".npy"
    save_libE_output(H, persis_info, history_file_name, nworkers, mess='Run completed')

    if software in _final_result:
        _final_result[software](H)


def _final_local_result(H):
    best, index = np.min(H['f']), np.argmin(H['f'])
    print("Minimum result:", H['x'][index], best)

def _final_global_result(H):
    print("Local Minima Found: ('x', 'f')")
    for lm in H[H['local_min']]:
        print(lm['x'], lm['f'])

_final_result = {
    'nlopt': _final_local_result,
    'aposmm': _final_global_result
}