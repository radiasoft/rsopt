from rsopt import mpi
from rsopt import parse
from rsopt.configuration import Configuration
from importlib import util
from pykern import pkio
from pykern import pkresource
from pykern import pkyaml
import pathlib
import datetime


def startup_sequence(config: str) -> Configuration:
    """Safely initialize rsopt accounting for the local MPI configuration (if any).

    Args:
        config:  (str) Path to configuration file that will be used

    Returns:(rsopt.configuration.configuration.Configuration) object

    """

    _local_opt_startup()
    config_yaml = parse.read_configuration_file(config)
    _config = parse.parse_yaml_configuration(config_yaml)
    mpi_environment = mpi.get_mpi_environment()
    if not mpi_environment:
        return _config
    else:
        if _config.options.nworkers != mpi_environment['nworkers']:
            print("`nworkers` in Config file does not match MPI communicator size.")
            print("MPI communicator size will be used to set up {} workers".format(mpi_environment['nworkers']))
            _config.options.nworkers = mpi_environment['nworkers']
        for k, v in mpi_environment.items():
            if hasattr(_config, k):
                _config.__setattr__(k, v)

    return _config


def _local_opt_startup():
    # TODO: Remove CLEANUP

    _OPT_SCHEMA = pkyaml.load_file(pkio.py_path(pkresource.filename('optimizer_schema.yml')))
    allowed_optimizer_list = [s for s, v in _OPT_SCHEMA.items() if v['type'] == 'local']
    available_opt = []
    for optimizer in allowed_optimizer_list:
        if optimizer == 'external':
            continue
        if util.find_spec(optimizer):
            available_opt.append(optimizer)

    import libensemble.gen_funcs
    _libensemble_path = pathlib.Path(libensemble.gen_funcs.__file__)
    # make sure .opt_modules.csv is removed for testing purposes
    _libensemble_path.parents[0].joinpath(libensemble.gen_funcs.rc._csv_path).unlink()
    with open(_libensemble_path.parents[0].joinpath(libensemble.gen_funcs.rc._csv_path), 'w') as ff:
        ff.write(','.join(available_opt))


    print("I made a CSV:", _libensemble_path.parents[0].joinpath(libensemble.gen_funcs.rc._csv_path))  # CLEANUP
    print("I made it just before: ",  datetime.datetime.now())  # CLEANUP


def local_optimizer(config):
    from rsopt.libe_tools.optimizer import libEnsembleOptimizer
    opt = libEnsembleOptimizer()
    opt.load_configuration(config)

    return opt


def grid_sampler(config):
    from rsopt.libe_tools import sampler
    sample = sampler.GridSampler()
    sample.load_configuration(config)

    return sample


def single_sampler(config):
    from rsopt.libe_tools import sampler
    sample = sampler.SingleSample()
    sample.load_configuration(config)

    return sample


def lh_sampler(config):
    from rsopt.libe_tools import sampler
    sample = sampler.LHSampler()
    sample.load_configuration(config)

    return sample


def restart_sampler(config, history):
    from rsopt.libe_tools import sampler
    sample = sampler.RestartSampler(restart_from=history)
    sample.load_configuration(config)

    return sample


def aposmm_optimizer(config):
    from rsopt.libe_tools.optimizer_aposmm import AposmmOptimizer
    opt = AposmmOptimizer()
    opt.load_configuration(config)

    return opt


def nsga2_optimizer(config):
    from rsopt.libe_tools.optimizer_nsga2 import EvolutionaryOptimizer
    opt = EvolutionaryOptimizer()
    opt.load_configuration(config)

    return opt


def pysot_optimizer(config):
    from rsopt.libe_tools.optimizer_pysot import PysotOptimizer
    opt = PysotOptimizer()
    opt.load_configuration(config)

    return opt


def dlib_optimizer(config):
    from rsopt.libe_tools.optimizer_dlib import DlibOptimizer
    opt = DlibOptimizer()
    opt.load_configuration(config)

    return opt


def mobo_optimizer(config):
    from rsopt.libe_tools.optimizer_mobo import MoboOptimizer
    opt = MoboOptimizer()
    opt.load_configuration(config)

    return opt


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
