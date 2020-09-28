import numpy as np
from rsopt.libe_tools.optimizer import libEnsembleOptimizer
from rsopt.libe_tools.optimizer import set_dtype_dimension
from rsopt.libe_tools import tools
from rsopt.libe_tools.generator_functions import utility_generators

mesh_sampler_gen_out =[('x', float, None)]

# TODO: could expand the parameter spec to have an optional sample field to read from
# TODO: Haven't checked if multijob run will work correctly

class GridSampler(libEnsembleOptimizer):

    def __init__(self):
        super().__init__()

    def _configure_optimizer(self):
        self.nworkers = self._config.options.nworkers
        self.exact_mesh = self._config.options.mesh_file

        if self.exact_mesh:
            mesh = np.load(self.exact_mesh)
        else:
            mesh = self._define_mesh_parameters()

        user_keys = {
                     'mesh_definition': mesh,
                     'exact_mesh': True if self.exact_mesh else False
                     }

        gen_out = [set_dtype_dimension(dtype, len(mesh)) for dtype in mesh_sampler_gen_out]

        # for key, val in self._options.items():
        #     user_keys[key] = val

        self.gen_specs.update({'gen_f': utility_generators.generate_mesh,
                               'in': [],
                               'out': gen_out,
                               'user': user_keys})

    def _configure_persistant_info(self):
        # _configure_specs must have been already called
        self.persis_info = tools.create_empty_persis_info(self.libE_specs)

    def _define_mesh_parameters(self):
        mesh_parameters = []

        for lb, ub, s in zip(self.lb, self.ub, self._config.get_parameters_list('get_samples')):
            mp = [lb, ub, s]
            mesh_parameters.append(mp)

        return mesh_parameters
