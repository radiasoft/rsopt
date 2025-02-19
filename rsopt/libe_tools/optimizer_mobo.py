from rsopt.libe_tools import tools
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.generator_functions.persistent_xopt_bo import persistent_mobo
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens

mobo_gen_out = [('x', float, None), ]


class MoboOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):
        gen_out = [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in mobo_gen_out]
        user_keys = {'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds,
                     'dim': self._config.dimension,
                     'processes': self._config.options.nworkers - 1,
                     'constraints': self._config.options.software_options.constraints,
                     'ref': self._config.options.software_options.reference_point,
                     'min_calc_to_remodel': self._config.options.software_options.min_calc_to_remodel,
                     }

        self.gen_specs.update({'gen_f': persistent_mobo,
                               'persis_in': self._config.options.method.persis_in +
                                            [n[0] for n in gen_out],
                               'out': gen_out,
                               'user': user_keys})

    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': only_persistent_gens,
                                 'out': [('given_back', bool)],
                                 'user': {'async_return': True, 'active_recv_gen': True}})

    def _configure_specs(self):
        self.nworkers = self._config.options.nworkers
        super(MoboOptimizer, self)._configure_specs()
