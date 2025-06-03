import numpy as np
from rsopt.libe_tools import tools
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.interface import get_local_optimizer_method
from libensemble.gen_funcs.persistent_aposmm import aposmm
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc


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

def format_user_specs(rsopt_options: "rsopt.configuration.schemas.options.OptionsExit"):
    # aposmm has different conventions on where local optimizer arguments go in the user_specs dictionary
    # some are placed directly in the top level. Other's get a sub-dictionary named after the local optimizer.

    user_options = {**rsopt_options.software_options.dict(exclude='local_opt_options`')}
    if rsopt_options.method.parent_software == 'nlopt':
        # nlopt does not handle values of None if a number was expected, so unset fields should not be passed
        user_options = {**user_options, **rsopt_options.software_options.local_opt_options.dict(exclude_unset=True)}
    elif rsopt_options.method.parent_software in ('scipy', 'dfols'):
        k = '{}_kwargs'.format(rsopt_options.method.parent_software)
        user_options[k] = rsopt_options.software_options.local_opt_options.dict()

    return user_options

class AposmmOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):
        gen_out = [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in aposmm_gen_out]
        if self._config.options.software_options.load_start_sample:
            self.H0 = process_start_sample(self._config.options.software_options.load_start_sample)

        user_specs = format_user_specs(self._config.options)
        user_keys = {'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds,
                     'localopt_method': get_local_optimizer_method(self._config.options.method.name,
                                                                   self._config.options.method.parent_software
                                                                   ),
                     **user_specs}

        self.gen_specs.update({'gen_f': aposmm,
                               'persis_in': self._config.options.method.persis_in +
                                            [n[0] for n in gen_out],
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
