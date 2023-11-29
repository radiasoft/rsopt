import rsopt.configuration.configuration
from rsopt import run


@run.cleaup
def configuration(config: str) -> ("numpy.ndarray", dict, "rsopt.configuration.configuration.Configuration") :
    """Runs a sampling job.

    A sampling job will be started based on the content of the configuration file.
    The configuration file should have the software field in options set to one of:
      mesh_scan, lh_scan

    :param config: (str) Name of configuration file to use
    :return: None
    """
    _config = run.startup_sequence(config)
    sampler_type = _config.options.NAME
    runner = run.sample_modes[sampler_type](_config)

    H, persis_info, _ = runner.run()

    return H, persis_info, _config

@run.cleaup
def start(config, n=1):
    """Run a single pass through the run chain in the configuration file.

    All settings are applied. Any parameters in the configuration are set to the value in `start`.
    The setting for `software` is ignored in this mode.
    The run chain can be repeated multiple times. All settings and parameters will always be set to
    their respective `start` values each time but this may be useful if there are random processes
    in the simulation.

    Args:
        config: (str) Name of configuration file to use
        n: (int) Number of times to run the chain. Default is 1.

    Returns:

    """
    _config = run.startup_sequence(config)

    # SingleSampler hardcodes nworkers to 1 and ignores user input
    _config.options.nworkers = min((_config.options.nworkers, n))
    runner = run.single_sampler(_config)
    H, persis_info, _ = runner.run()

    return H, persis_info, _config

@run.cleaup
def restart(config, history, rerun_failed=''):
    _config = run.startup_sequence(config)
    runner = run.restart_sampler(_config, history)
    H, persis_info, _ = runner.run()

    return H, persis_info, _config
