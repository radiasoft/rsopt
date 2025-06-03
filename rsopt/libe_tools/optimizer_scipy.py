from rsopt.libe_tools import tools
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.generator_functions.local_opt_generator import persistent_local_opt
from rsopt.libe_tools.interface import get_local_optimizer_method

# dtype dimensions > 1 are set at run time
persistent_local_opt_gen_out = [('x', float, None),
                                ('x_on_cube', float, None),
                                ('sim_id', int),
                                ('local_pt', bool)]

class SciPyOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):
        local_opt_method = get_local_optimizer_method(self._config.options.method.name,
                                                      self._config.options.software)
        gen_out = [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in persistent_local_opt_gen_out]
        user_keys = {'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds,
                     'initial_sample_size': 1,
                     'xstart': self._config.start,
                     'localopt_method': local_opt_method,
                     'scipy_kwargs': {**self._config.options.software_options.model_dump(exclude='grad_dimensions')},
                     'opt_return_codes': self._config.options.method._opt_return_code
                     }

        self.gen_specs.update({'gen_f': persistent_local_opt,
                               'persis_in': self._config.options.method.persis_in +
                                            [n[0] for n in gen_out],
                               'out': gen_out,
                               'user': user_keys})
