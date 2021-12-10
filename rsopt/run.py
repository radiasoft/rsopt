from rsopt.libe_tools.sampler import GridSampler, SingleSample, LHSampler
from rsopt import mpi
from rsopt import parse


def startup_sequence(config):
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


def local_optimizer(config):
    from rsopt.libe_tools.optimizer import libEnsembleOptimizer
    opt = libEnsembleOptimizer()
    opt.load_configuration(config)

    return opt


def grid_sampler(config):
    sample = GridSampler()
    sample.load_configuration(config)

    return sample


def single_sampler(config):
    sample = SingleSample()
    sample.load_configuration(config)

    return sample


def lh_sampler(config):
    sample = LHSampler()
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