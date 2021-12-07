import numpy as np
from rsopt.libe_tools.optimizer import libEnsembleOptimizer
from rsopt.libe_tools.optimizer import set_dtype_dimension
from rsopt.libe_tools import tools
from rsopt.libe_tools.generator_functions import utility_generators
from libensemble.tools import add_unique_random_streams
from libensemble.gen_funcs.sampling import latin_hypercube_sample
mesh_sampler_gen_out = [('x', float, None)]
lh_sampler_gen_out = [('x', float, None)]

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
            sim_max = mesh.size
        else:
            mesh, sim_max = self._define_mesh_parameters()

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

        # Overwrite any use specified exit criteria and set based on scan
        self._config.options.exit_criteria = None
        self.exit_criteria = {'sim_max': sim_max}


    def _configure_allocation(self):
        # If not setting alloc_specs it must be None and not empty dict
        self.alloc_specs = None

    def _configure_persistant_info(self):
        # _configure_specs must have been already called
        self.persis_info = tools.create_empty_persis_info(self.libE_specs)

    def _define_mesh_parameters(self):
        mesh_parameters = []
        size = 1
        for lb, ub, st, s in zip(self.lb, self.ub, self.start, self._config.get_parameters_list('get_samples')):
            if s == 1:
                mp = [st, st, s]
            else:
                mp = [lb, ub, s]
            mesh_parameters.append(mp)
            size *= s

        return mesh_parameters, size

class SingleSample(GridSampler):
    # Run a single point using start values of parameters - or no parameters at all
    # mesh_file is ignored, even if given
    def _define_mesh_parameters(self):
        mesh_parameters = []
        size = 1

        for lb, ub, s in zip(self.lb, self.ub, self.start):
            mesh_parameters.append(s)
        mesh_parameters = np.array(mesh_parameters).reshape(len(mesh_parameters), 1)

        return mesh_parameters, size

    def _configure_optimizer(self):
        self.nworkers = 1

        mesh, sim_max = self._define_mesh_parameters()

        user_keys = {
                     'mesh_definition': mesh,
                     'exact_mesh': True
                     }

        gen_out = [set_dtype_dimension(dtype, len(mesh)) for dtype in mesh_sampler_gen_out]

        # for key, val in self._options.items():
        #     user_keys[key] = val

        self.gen_specs.update({'gen_f': utility_generators.generate_mesh,
                               'in': [],
                               'out': gen_out,
                               'user': user_keys})

        # Overwrite any use specified exit criteria and set based on scan
        self._config.options.exit_criteria = None
        self.exit_criteria = {'sim_max': sim_max}

class LHSampler(libEnsembleOptimizer):

    def __init__(self):
        super().__init__()

    def _configure_optimizer(self):
        self.nworkers = self._config.options.nworkers

        user_keys = {'gen_batch_size': self._config.options.batch_size,
                     'lb': self.lb,
                     'ub': self.ub}

        gen_out = [set_dtype_dimension(dtype, len(self.lb)) for dtype in lh_sampler_gen_out]

        # for key, val in self._options.items():
        #     user_keys[key] = val

        self.gen_specs.update({'gen_f': latin_hypercube_sample,
                               'in': [],
                               'out': gen_out,
                               'user': user_keys})

        # Overwrite any use specified exit criteria and set based on scan
        self._config.options.exit_criteria = None
        self.exit_criteria = {'sim_max': self._config.options.batch_size}

    def _configure_allocation(self):
        # If not setting alloc_specs it must be None and not empty dict
        self.alloc_specs = None

    def _configure_persistant_info(self):
        # _configure_specs must have been already called
        self.persis_info = add_unique_random_streams({}, self.nworkers + 1, seed=self._config.options.seed)
