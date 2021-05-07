from rsopt.libe_tools import optimizer
from rsopt.libe_tools.interface import get_local_optimizer_method
from libensemble.gen_funcs.persistent_deap_nsga2 import deap_nsga2
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens

# TODO: make set_optimizer a member of Optimizer and have a Setup like class selection scheme
#  based on arguments of set_optimizer

# set_optimizer method: software is nsga2 and method does not need to be set currently

# dimension for individual set at run time
nsga2_gen_out = [('individual', float, None), ('generation', int)]
_DEFAULT_WEIGHT = (-1.0, )


class EvolutionaryOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self):
        super().__init__()

    def _configure_optimizer(self):

        gen_out = [optimizer.set_dtype_dimension(dtype, self.dimension) for dtype in nsga2_gen_out]

        user_keys = {'lb': self.lb,
                     'ub': self.ub,
                     'pop_size': self._config.options.pop_size,
                     **self._config.options.software_options}

        # NSGA2 parameters
        assert self._config.options.n_objectives > 0, "n_objectives must be set in options to a number > 0"

        self._generator_defaults = {
            # Set to DEAP implementation defaults
            'weights': _DEFAULT_WEIGHT * self._config.options.n_objectives,
            'cxpb': 0.9,  # probability two individuals are crossed
            'eta': 20.0,  # large eta = low variation in children
            'indpb': 1.0 / self._config.options.n_objectives  # Mutation probability
        }

        # If user didn't set keys contained in _generator_defaults though software_options then set them now
        for key, val in self._generator_defaults.items():
            user_keys.setdefault(key, val)

        self.gen_specs.update({'gen_f': deap_nsga2,
                               'in': ['sim_id', 'generation', 'individual', 'fitness_values'],
                               'out': gen_out,
                               'user': user_keys})

    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': only_persistent_gens,
                                 'out': [('given_back', bool)]})

    def _configure_specs(self):
        self.nworkers = self._config.options.nworkers
        super(EvolutionaryOptimizer, self)._configure_specs()