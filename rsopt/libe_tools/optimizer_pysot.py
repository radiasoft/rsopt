import numpy as np
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.generator_functions.persistent_pysot import persistent_pysot
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens


pysot_gen_out = [('x', float, None), ]


class PysotOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self):
        super().__init__()

    def _configure_optimizer(self):
        gen_out = [optimizer.set_dtype_dimension(dtype, self.dimension) for dtype in pysot_gen_out]
        user_keys = {'lb': self.lb,
                     'ub': self.ub,
                     'dim': self._config.get_dimension(),
                     'max_evals': np.max([val for val in self._config.options.exit_criteria.values()]).astype(int).astype(object),
                     'threads': self._config.options.nworkers - 1,
                     **self._config.options.software_options}

        self.gen_specs.update({'gen_f': persistent_pysot,
                               'in': [],
                               'out': gen_out,
                               'user': user_keys})

    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': only_persistent_gens,
                                 'out': [('given_back', bool)],
                                 'user': {'async_return': True, 'active_recv_gen': True}})
