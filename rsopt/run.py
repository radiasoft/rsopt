# Functions to run a call from originating from pkcli
# This is just a temporary setup. libEnsembleOptimizer shouldn't actually be tied to execution mode
# It is instantiated because nlopt was requested
# THe executor will be setup separately based off 'execution_type' in YAML and registered with libEnsembleOptimizer
from rsopt.libe_tools.optimizer import libEnsembleOptimizer
from rsopt.libe_tools.optimizer_aposmm import AposmmOptimizer

def local_optimizer(config):
    opt = libEnsembleOptimizer()
    opt.load_configuration(config)

    return opt  #.run()

def aposmm_optimizer(config):
    opt = AposmmOptimizer()
    opt.load_configuration(config)

    return opt  #.run()

# These names have to line up with accepted values for setup.execution_type
# Another place where shared names are imported from common source
run_modes = {
    'nlopt': local_optimizer,
    'aposmm': aposmm_optimizer
}