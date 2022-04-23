from rsopt.libe_tools import tools
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.generator_functions.persistent_mobo import persistent_mobo
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens

mobo_gen_out = [('x', float, None), ]


class MoboOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self):
        super().__init__()

    def _configure_optimizer(self):
        gen_out = [tools.set_dtype_dimension(dtype, self.dimension) for dtype in mobo_gen_out]
        user_keys = {'lb': self.lb,
                     'ub': self.ub,
                     'dim': self._config.get_dimension(),
                     'processes': self._config.options.nworkers - 1,
                     'budget': self._config.options.exit_criteria['sim_max'],
                     # TODO: or set budget directly
                     'constraints': self._config.options.software_options.get('constraints', {}),
                     'ref': self._config.options.reference,
                     **self._config.options.software_options}

        self.gen_specs.update({'gen_f': persistent_mobo,
                               'persis_in': self._set_persis_in(self._config.software, self._config.method) +
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
