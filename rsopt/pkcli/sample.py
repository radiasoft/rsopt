import rsopt.parse as parse
import numpy as np
import os
from rsopt.run import grid_sampler
from libensemble.tools import save_libE_output

def configuration(config):
    config_yaml = parse.read_configuration_file(config)
    _config = parse.parse_yaml_configuration(config_yaml)

    # TODO: This is hard coded to serial for testing right now
    runner = grid_sampler(_config)

    H, persis_info, _ = runner.run()

    filename = os.path.splitext(config)[0]
    history_file_name = "H_sample_" + filename + ".npy"
    save_libE_output(H, persis_info, history_file_name, 2, mess='Sampler completed')
