from rsopt.configuration.schemas import configuration
from ruamel.yaml import YAML
import importlib.util
import os
import pathlib
import rsopt.util
from rsopt import run_archive

# path from libEnsemble install directory to .opt_modules.csv
# This must be hardcoded because importing libensemble.gen_funcs to check the expected file name
# will instantiate gen_funcs.RC before .opt_modules.csv is created by rsopt
_OPT_MODULES_RELPATH = './gen_funcs/.opt_modules.csv'

# Ensures that pre- and post-processing or objective functions do not encounter pickle errors on Mac
if os.uname().sysname == 'Darwin':
    from multiprocessing import set_start_method
    set_start_method('fork', force=True)


def startup_sequence(config: configuration.ConfigurationOptimize or configuration.ConfigurationSample,
                     config_path: str or pathlib.Path or None = None) -> (
        configuration.ConfigurationOptimize or configuration.ConfigurationSample):
    """Safely initialize rsopt accounting for the local MPI configuration (if any).

    `options.run_dir` is made absolute and checked first, so that a run_dir already holding output fails before any
    slow setup.

    Args:
        config: (rsopt.configuration.configuration.Configuration) Parsed configuration
        config_path: (str or pathlib.Path or None) Path to the configuration file that `config` was loaded from

    Returns:(rsopt.configuration.configuration.Configuration) object

    Raises:
        rsopt.run_archive.RunDirectoryError: if run_dir exists and is not an empty directory.
    """
    if config_path is not None:
        config.config_path = pathlib.Path(config_path).resolve()
    run_dir = run_archive.resolve_run_dir(config.options)
    config.options.run_dir = str(run_dir)
    # TODO(MPI): config.is_manager is always True until MPI detection below is restored. Under MPI comms,
    #  worker ranks would otherwise see the manager's new directory and fail.
    if config.is_manager:
        run_archive.check_run_dir_at_startup(run_dir, config.config_path)

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


def cleanup(config_path, H, persis_info, config):
    if config.is_manager:
        history, _ = rsopt.util.save_final_history(config, config_path, H, persis_info, message='Run finished')
        if config.options.copy_final_logs:
            rsopt.util.copy_final_history(config.options, history)


def _local_opt_startup() -> None:
    """Write .opt_modules.csv

    Returns:

    """
    _OPT_SCHEMA = YAML().load(rsopt.util.package_data_path() / 'optimizer_schema.yml')
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
    opt = libEnsembleOptimizer(config)

    return opt

def local_optimizer_scipy(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_scipy import SciPyOptimizer
    opt = SciPyOptimizer(config)

    return opt

def local_optimizer_nlopt(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_nlopt import NloptOptimizer
    opt = NloptOptimizer(config)

    return opt

def grid_sampler(config: configuration.ConfigurationSample):
    from rsopt.libe_tools import sampler
    sample = sampler.GridSampler(config)

    return sample


def single_sampler(config: configuration.ConfigurationSample, n:int = 1):
    from rsopt.libe_tools import sampler
    sample = sampler.SingleSample(config, sampler_repeats=n)

    return sample


def lh_sampler(config: configuration.ConfigurationSample):
    from rsopt.libe_tools import sampler
    sample = sampler.LHSampler(config)

    return sample


def restart_sampler(config: configuration.ConfigurationSample, history: str):
    from rsopt.libe_tools import sampler
    sample = sampler.RestartSampler(config, restart_from=history)

    return sample


def aposmm_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_aposmm import AposmmOptimizer
    opt = AposmmOptimizer(config)

    return opt


def nsga2_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_nsga2 import EvolutionaryOptimizer
    opt = EvolutionaryOptimizer(config)

    return opt


def pysot_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_pysot import PysotOptimizer
    opt = PysotOptimizer(config)

    return opt


def dlib_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_dlib import DlibOptimizer
    opt = DlibOptimizer(config)

    return opt


def pybobyqa_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_pybobyqa import PybobyqaOptimizer
    opt = PybobyqaOptimizer(config)

    return opt


def mobo_optimizer(config: configuration.ConfigurationOptimize):
    from rsopt.libe_tools.optimizer_mobo import MoboOptimizer
    opt = MoboOptimizer(config)

    return opt

# TODO: Can these be more strongly tied to the models so I don't have to reuse the names here?
# These names have to line up with accepted values for setup.execution_type
# Another place where shared names are imported from common source
run_modes = {
    'nlopt': local_optimizer_nlopt,
    'dfols': local_optimizer,
    'scipy': local_optimizer_scipy,
    'aposmm': aposmm_optimizer,
    'nsga2': nsga2_optimizer,
    'pysot': pysot_optimizer,
    'dlib': dlib_optimizer,
    'mobo': mobo_optimizer,
    'pybobyqa': pybobyqa_optimizer
}

sample_modes = {
    'mesh_scan': grid_sampler,
    'lh_scan': lh_sampler
}
