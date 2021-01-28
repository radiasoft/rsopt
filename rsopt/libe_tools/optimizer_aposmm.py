from rsopt.libe_tools import optimizer
from rsopt.libe_tools.interface import get_local_optimizer_method
from libensemble.gen_funcs.persistent_aposmm import aposmm
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc

# TODO: make set_optimizer a member of Optimizer and have a Setup like class selection scheme
#  based on arguments of set_optimizer

# set_optimizer method: software is aposmm and method is local_opt method, options go to aposmm

# dimension for x and x_on_cube set at run time
aposmm_gen_out =  [('x', float, None), ('x_on_cube', float, None), ('sim_id', int),
           ('local_min', bool), ('local_pt', bool)]

class AposmmOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self):
        super().__init__()

        # # required APOSMM options for gen_specs['user']
        # self.initial_sample_size = None
        # # optional APOSMM options for gen_specs['user']
        # #   default specified here:
        # self.max_active_runs = self.nworkers - 1
        # #   default left to APOSMM setting:

    def _configure_optimizer(self):
        gen_out = [optimizer.set_dtype_dimension(dtype, self.dimension) for dtype in aposmm_gen_out]

        user_keys = {'lb': self.lb,
                     'ub': self.ub,
                     'initial_sample_size': self._config.options.initial_sample_size,
                     'localopt_method': get_local_optimizer_method(self._config.method, self._config.software),
                     **self._config.options.software_options}

        for key, val in self._options.items():
            user_keys[key] = val
        self.gen_specs.update({'gen_f': aposmm,
                     'in': [],
                     'out': gen_out,
                     'user': user_keys})


    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': persistent_aposmm_alloc,
                                 'out': [('given_back', bool)],
                                 'user': {'batch_mode': True}})

    def _configure_specs(self):
        self.nworkers = self._config.options.nworkers
        super(AposmmOptimizer, self)._configure_specs()
