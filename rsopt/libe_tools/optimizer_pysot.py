from rsopt.libe_tools import tools
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.generator_functions.persistent_pysot import persistent_pysot
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens


pysot_gen_out = [('x', float, None), ]
DEFAULT_MAX_EVALS = 1e6

class PysotOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):
        gen_out = [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in pysot_gen_out]
        user_keys = {'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds,
                     'dim': self._config.dimension,
                     # libEnsemble is controlling when to stop running so give the exact max if libEnsemble has it
                     # otherwise set max_evals very high so that pySOT should run until stopped externally
                     'max_evals': self._config.options.exit_criteria.sim_max or DEFAULT_MAX_EVALS,
                     **self._config.options.software_options.model_dump()}

        self.gen_specs.update({'gen_f': persistent_pysot,
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
        super(PysotOptimizer, self)._configure_specs()
