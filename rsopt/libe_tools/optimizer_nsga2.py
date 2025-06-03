from rsopt.libe_tools import tools
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.generator_functions.persistent_deap_nsga2 import deap_nsga2
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens


# dimension for individual set at run time
nsga2_gen_out = [('individual', float, None), ('generation', int), ('last_points', bool)]
_DEFAULT_WEIGHT = (-1.0, )


class EvolutionaryOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):

        gen_out = [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in nsga2_gen_out]

        if 'indpb' not in self._config.options.software_options.model_fields_set:
            self._config.options.software_options.indpb /= self._config.dimension

        user_keys = {'lb': list(self._config.lower_bounds),  # DEAP requires lists
                     'ub': list(self._config.upper_bounds),
                     'indiv_size': self._config.dimension,
                     'pop_size': self._config.options.software_options.pop_size,
                     'cxpb': self._config.options.software_options.cxpb,
                     'eta': self._config.options.software_options.eta,
                     'indpb': self._config.options.software_options.indpb,
                     'weights': _DEFAULT_WEIGHT * self._config.options.software_options.n_objectives,
                     }

        self.gen_specs.update({'gen_f': deap_nsga2,
                               'persis_in': self._config.options.method.persis_in +
                                            [n[0] for n in gen_out],
                               'in': ['sim_id', 'generation', 'individual', 'fitness_values'],
                               'out': gen_out,
                               'user': user_keys})

    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': only_persistent_gens, 'user': {'give_all_with_same_priority': True}})

    def _configure_specs(self):
        self.nworkers = self._config.options.nworkers
        super(EvolutionaryOptimizer, self)._configure_specs()