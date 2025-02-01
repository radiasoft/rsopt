import numpy as np
from rsopt.libe_tools.optimizer import libEnsembleOptimizer
from rsopt.libe_tools.tools import set_dtype_dimension
from rsopt.libe_tools import tools
from rsopt.libe_tools.generator_functions import utility_generators
from libensemble.tools import add_unique_random_streams
from libensemble.gen_funcs.sampling import latin_hypercube_sample
from libensemble.alloc_funcs.give_pregenerated_work import give_pregenerated_sim_work

mesh_sampler_gen_out = [('x', float, None)]
lh_sampler_gen_out = [('x', float, None)]


class GridSampler(libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):
        self.nworkers = self._config.options.nworkers
        self.exact_mesh = self._config.options.software_options.mesh_file
        sampler_repeats = int(self._config.options.software_options.sampler_repeats)

        if self.exact_mesh:
            # Mesh should have shape (number of parameters, number of samples)
            mesh = np.load(self.exact_mesh)
            sim_max = mesh.shape[1]
        else:
            mesh, sim_max = self._define_mesh_parameters()

        user_keys = {
                     'mesh_definition': mesh,
                     'exact_mesh': True if self.exact_mesh else False,
                     'sampler_repeats': sampler_repeats
                     }

        gen_out = [set_dtype_dimension(dtype, len(mesh)) for dtype in mesh_sampler_gen_out]

        # for key, val in self._options.items():
        #     user_keys[key] = val

        self.gen_specs.update({'gen_f': utility_generators.generate_mesh,
                               'in': [],
                               'out': gen_out,
                               'user': user_keys})

        self.exit_criteria = {'sim_max': sim_max * sampler_repeats}

    def _configure_allocation(self):
        self.alloc_specs = {}

    def _configure_persistant_info(self):
        # _configure_specs must have been already called
        self.persis_info = add_unique_random_streams({}, self.nworkers + 1, seed=self._config.options.seed)

    def _define_mesh_parameters(self):
        mesh_parameters = []
        size = 1
        for lb, ub, st, s in zip(self._config.lower_bounds, self._config.upper_bounds, self._config.start,
                                 self._config.samples):
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

    def __init__(self, config_model, sampler_repeats: int = 1):
        """

        Args:
            sampler_repeats: (int) Default 1. Rerun the start point this many times.
        """
        super().__init__(config_model)
        self.sampler_repeats = sampler_repeats

    def _define_mesh_parameters(self):
        mesh_parameters = []
        size = self.sampler_repeats

        for lb, ub, s in zip(self._config.lower_bounds, self._config.upper_bounds, self._config.start):
            mesh_parameters.append(s)
        mesh_parameters = np.array(mesh_parameters).reshape(len(mesh_parameters), 1)
        mesh_parameters = np.repeat(mesh_parameters, repeats=self.sampler_repeats, axis=1)

        return mesh_parameters, size

    def _configure_optimizer(self):
        self.nworkers = self._config.options.nworkers

        mesh, sim_max = self._define_mesh_parameters()

        user_keys = {
                     'mesh_definition': mesh,
                     'exact_mesh': True,
                     # Sampler repeats was already handled by self._define_mesh_parameters
                     # Set to 1 here so the generator does not double up repetitions.
                     'sampler_repeats': 1
                     }

        gen_out = [set_dtype_dimension(dtype, len(mesh)) for dtype in mesh_sampler_gen_out]

        # for key, val in self._options.items():
        #     user_keys[key] = val

        self.gen_specs.update({'gen_f': utility_generators.generate_mesh,
                               'in': [],
                               'out': gen_out,
                               'user': user_keys})

        self.exit_criteria = {'sim_max': sim_max}

    def _configure_specs(self):
        super(SingleSample, self)._configure_specs()
        # single sample overrides the software in the config file to use sampler so we need to force no zero rec workers
        self.libE_specs['zero_resource_workers'] = []


class LHSampler(libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):
        self.nworkers = self._config.options.nworkers

        user_keys = {'gen_batch_size': self._config.options.batch_size,
                     'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds}

        gen_out = [set_dtype_dimension(dtype, len(self._config.lower_bounds)) for dtype in lh_sampler_gen_out]

        # for key, val in self._options.items():
        #     user_keys[key] = val

        self.gen_specs.update({'gen_f': latin_hypercube_sample,
                               'in': [],
                               'out': gen_out,
                               'user': user_keys})

        self.exit_criteria = {'sim_max': self._config.options.batch_size}

    def _configure_allocation(self):
        self.alloc_specs = {}

    def _configure_persistant_info(self):
        # _configure_specs must have been already called
        self.persis_info = add_unique_random_streams({}, self.nworkers + 1, seed=self._config.options.seed)


restart_alloc_out = [('x', float, None), ]


class RestartSampler(libEnsembleOptimizer):

    def __init__(self, config_model, restart_from):
        self.restart_from = restart_from
        super().__init__(config_model)

        self._set_evaluation_points()

    def _configure_optimizer(self):
        self.nworkers = self._config.options.nworkers

        self.exit_criteria = {'sim_max': self.H0.size}

    def _configure_allocation(self):
        self.alloc_specs = {'alloc_f': give_pregenerated_sim_work,
                            'out': [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in restart_alloc_out]}

    def _configure_persistant_info(self):
        # No persis info needs to be maintained
        self.persis_info = {}

    def _set_evaluation_points(self):
        H_candidates = np.load(self.restart_from)
        H_new = tools.filter_completed_history(H_candidates)
        self.H0 = H_new
