import numpy as np
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.interface import get_local_optimizer_method
from libensemble.gen_funcs.persistent_aposmm import aposmm
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc

# TODO: make set_optimizer a member of Optimizer and have a Setup like class selection scheme
#  based on arguments of set_optimizer

# set_optimizer method: software is aposmm and method is local_opt method, options go to aposmm

# dimension for x and x_on_cube set at run time
aposmm_gen_out = [('x', float, None), ('x_on_cube', float, None), ('sim_id', int),
                  ('local_min', bool), ('local_pt', bool)]


def split_method(method_name):
    software, method = method_name.split('.')
    return software, method


def process_start_sample(numpy_file):
    H0 = np.load(numpy_file)
    if 'given_back' not in H0.dtype.names:
        # Assume it came from a scan and just set given_back as all successful
        new_dtype = np.dtype(H0.dtype.descr + [('given_back', bool)])
        Hc = np.zeros(H0.size, new_dtype)
        for field in H0.dtype.names:
            Hc[field] = H0[field]

        Hc['given_back'] = True

        return Hc[Hc['returned']]

    return H0[H0['returned'] & H0['given_back']]


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
        if self._config.options.load_start_sample:
            self.H0 = process_start_sample(self._config.options.load_start_sample)
        software, method = split_method(self._config.method)
        user_keys = {'lb': self.lb,
                     'ub': self.ub,
                     'initial_sample_size': self._config.options.initial_sample_size,
                     'localopt_method': get_local_optimizer_method(method, software),
                     **self._config.options.software_options}

        for key, val in self._options.items():
            user_keys[key] = val
        self.gen_specs.update({'gen_f': aposmm,
                               # TODO: This will need to be updated if other options beyond nlopt are added (
                               'in': ['x', 'f', 'local_pt', 'sim_id', 'returned', 'x_on_cube', 'local_min'],
                               'out': gen_out,
                               'user': user_keys})

    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': persistent_aposmm_alloc,
                                 'out': [('given_back', bool)],
                                 'user': {}})

    def _configure_specs(self):
        self.nworkers = self._config.options.nworkers
        super(AposmmOptimizer, self)._configure_specs()
