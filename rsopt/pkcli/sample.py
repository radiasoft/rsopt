import rsopt.parse as parse
import os
from rsopt.run import grid_sampler, single_sampler
from libensemble.tools import save_libE_output

def configuration(config):
    config_yaml = parse.read_configuration_file(config)
    _config = parse.parse_yaml_configuration(config_yaml)

    try:
        nworkers = _config.options.nworkers
    except AttributeError:
        # Sampler defaults to 1 worker if not set
        nworkers = 1

    runner = grid_sampler(_config)

    H, persis_info, _ = runner.run()

    filename = os.path.splitext(config)[0]
    history_file_name = "H_sample_" + filename + ".npy"
    save_libE_output(H, persis_info, history_file_name, nworkers, mess='Sampler completed')

def start(config):
    config_yaml = parse.read_configuration_file(config)
    _config = parse.parse_yaml_configuration(config_yaml)


    # SingleSampler hardcodes nworkers to 1 and ignores user input
    nworkers = 1

    runner = single_sampler(_config)

    H, persis_info, _ = runner.run()

    filename = os.path.splitext(config)[0]
    history_file_name = "H_sample_" + filename + ".npy"
    save_libE_output(H, persis_info, history_file_name, nworkers, mess='Ran start point')