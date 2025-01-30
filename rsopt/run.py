from rsopt import mpi
from rsopt.configuration.schemas import configuration
from pykern import pkio
from pykern import pkresource
from pykern import pkyaml
import functools
import importlib.util
import os
import pathlib
import rsopt.util

# path from libEnsemble install directory to .opt_modules.csv
# This must be hardcoded because importing libensemble.gen_funcs to check the expected file name
# will instantiate gen_funcs.RC before .opt_modules.csv is created by rsopt
_OPT_MODULES_RELPATH = './gen_funcs/.opt_modules.csv'

# Ensures that pre- and post-processing or objective functions do not encounter pickle errors on Mac
if os.uname().sysname == 'Darwin':
    from multiprocessing import set_start_method
    set_start_method('fork', force=True)


def startup_sequence(config: configuration.ConfigurationOptimize or configuration.Configuration) -> (
        configuration.ConfigurationOptimize or configuration.Configuration):
    """Safely initialize rsopt accounting for the local MPI configuration (if any).

    Args:
        config:  (str) Path to configuration file that will be used

    Returns:(rsopt.configuration.configuration.Configuration) object

    """

    _local_opt_startup()

    # TODO: This does some important things for MPI management. Will need to think about how to store this information.
    # mpi_environment = mpi.get_mpi_environment()

    # TEMP
    mpi_environment = None

    if not mpi_environment:
        return config
    else:
        if config.options.nworkers != mpi_environment['nworkers']:
            print("`nworkers` in Config file does not match MPI communicator size.")
            print("MPI communicator size will be used to set up {} workers".format(mpi_environment['nworkers']))
            config.options.nworkers = mpi_environment['nworkers']
        for k, v in mpi_environment.items():
            if hasattr(config, k):
                config.__setattr__(k, v)

    return config


def cleaup(action):
    # Make inner's metadata look like action. Allows it to be registered with pkcli.
    @functools.wraps(action)
    def inner(*args, **kwargs):
        H, persis_info, config = action(*args, **kwargs)
        if config.is_manager:
            history, _ = rsopt.util.save_final_history(config, H, persis_info, message='Run finished')
            if config.options.copy_final_logs:
                rsopt.util.copy_final_logs(config.configuration_file, config.options, history)
    return inner


def _local_opt_startup() -> None:
    """Write .opt_modules.csv

    Returns:

    """
    _OPT_SCHEMA = pkyaml.load_file(pkio.py_path(pkresource.filename('optimizer_schema.yml')))
    allowed_optimizer_list = [s for s, v in _OPT_SCHEMA.items() if v['type'] == 'local']
    available_opt = []
    for optimizer in allowed_optimizer_list:
        if optimizer == 'external':
            continue
        if importlib.util.find_spec(optimizer):
            available_opt.append(optimizer)

    import libensemble
    _opt_modules_path = pathlib.Path(libensemble.__file__).parents[0].joinpath(_OPT_MODULES_RELPATH)
    try:
        with open(_opt_modules_path, 'w') as ff:
            ff.write(','.join(available_opt))
    except OSError:
        print("Writing .opt_modules.csv failed")

############
# These functions are split up to localize imports and remove the requirement that every optimization package be
# installed for rsopt to function
############

def local_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer import libEnsembleOptimizer
    opt = libEnsembleOptimizer()
    opt.load_configuration(config)

    return opt


def grid_sampler(config: configuration.Configuration):
    from rsopt.libe_tools import sampler
    sample = sampler.GridSampler()
    sample.load_configuration(config)

    return sample


def single_sampler(config: configuration.Configuration, n:int = 1):
    from rsopt.libe_tools import sampler
    sample = sampler.SingleSample(sampler_repeats=n)
    sample.load_configuration(config)

    return sample


def lh_sampler(config: configuration.Configuration):
    from rsopt.libe_tools import sampler
    sample = sampler.LHSampler()
    sample.load_configuration(config)

    return sample


def restart_sampler(config: configuration.Configuration, history: str):
    from rsopt.libe_tools import sampler
    sample = sampler.RestartSampler(restart_from=history)
    sample.load_configuration(config)

    return sample


def aposmm_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_aposmm import AposmmOptimizer
    opt = AposmmOptimizer()
    opt.load_configuration(config)

    return opt


def nsga2_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_nsga2 import EvolutionaryOptimizer
    opt = EvolutionaryOptimizer()
    opt.load_configuration(config)

    return opt


def pysot_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_pysot import PysotOptimizer
    opt = PysotOptimizer()
    opt.load_configuration(config)

    return opt


def dlib_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_dlib import DlibOptimizer
    opt = DlibOptimizer()
    opt.load_configuration(config)

    return opt


def mobo_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_mobo import MoboOptimizer
    opt = MoboOptimizer()
    opt.load_configuration(config)

    return opt

# TODO: Can these be more strongly tied to the models so I don't have to reuse the names here?
# These names have to line up with accepted values for setup.execution_type
# Another place where shared names are imported from common source
run_modes = {
    'nlopt': local_optimizer,
    'dfols': local_optimizer,
    'scipy': local_optimizer,
    'aposmm': aposmm_optimizer,
    'nsga2': nsga2_optimizer,
    'pysot': pysot_optimizer,
    'dlib': dlib_optimizer,
    'mobo': mobo_optimizer
}

sample_modes = {
    'mesh_scan': grid_sampler,
    'lh_scan': lh_sampler
}
