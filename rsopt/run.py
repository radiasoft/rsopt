from rsopt.libe_tools.optimizer import libEnsembleOptimizer
from rsopt.libe_tools.sampler import GridSampler, SingleSample, LHSampler
from rsopt.libe_tools.optimizer_aposmm import AposmmOptimizer
from rsopt.libe_tools.optimizer_nsga2 import EvolutionaryOptimizer


def local_optimizer(config):
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
    opt = AposmmOptimizer()
    opt.load_configuration(config)

    return opt


def nsga2_optimizer(config):
    opt = EvolutionaryOptimizer()
    opt.load_configuration(config)

    return opt

# These names have to line up with accepted values for setup.execution_type
# Another place where shared names are imported from common source
run_modes = {
    'nlopt': local_optimizer,
    'dfols': local_optimizer,
    'scipy': local_optimizer,
    'aposmm': aposmm_optimizer,
    'nsga2': nsga2_optimizer
}

sample_modes = {
    'mesh_scan': grid_sampler,
    'lh_scan': lh_sampler
}