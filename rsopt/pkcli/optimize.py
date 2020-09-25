import rsopt.parse as parse
import numpy as np
import os
from rsopt.run import local_optimizer
from libensemble.tools import save_libE_output


def configuration(config):
    config_yaml = parse.read_configuration_file(config)
    _config = parse.parse_yaml_configuration(config_yaml)

    # TODO: This is hard coded to serial for testing right now
    runner = local_optimizer(_config)

    H, persis_info, _ = runner.run()

    filename = os.path.splitext(config)[0]
    history_file_name = "H_" + filename + ".npy"
    save_libE_output(H, persis_info, history_file_name, 2, mess='Run completed')
    best, index = np.min(H['f']), np.argmin(H['f'])

    print("Minimum result:", H['x'][index], best)