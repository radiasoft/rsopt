from rsopt import run
from rsopt import util


def configuration(config):
    _config = run.startup_sequence(config)

    sampler_type = _config.options.NAME
    try:
        nworkers = _config.options.nworkers
    except AttributeError:
        # Sampler defaults to 1 worker if not set
        nworkers = 1

    runner = run.sample_modes[sampler_type](_config)
    H, persis_info, _ = runner.run()

    if _config.is_manager:
        util.save_final_history(config, _config, H, persis_info, nworkers, message='Sampler completed')


def start(config):
    _config = run.startup_sequence(config)

    # SingleSampler hardcodes nworkers to 1 and ignores user input
    nworkers = 1

    runner = run.single_sampler(_config)
    H, persis_info, _ = runner.run()
    if _config.is_manager:
        util.save_final_history(config, _config, H, persis_info, nworkers, message='Ran start point')