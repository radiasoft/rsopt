import uuid
import numpy as np
from rsopt.libe_tools.optimizer import libEnsembleOptimizer
from rsopt.libe_tools.tools import set_dtype_dimension
from rsopt.libe_tools import tools
from rsopt.libe_tools.generator_functions import utility_generators
from libensemble.tools import add_unique_random_streams
from rsopt.libe_tools.tools import _total_scan_entries
from libensemble.gen_funcs.sampling import latin_hypercube_sample
from libensemble.alloc_funcs.give_pregenerated_work import give_pregenerated_sim_work

# mesh sampler datatype must be object to support possibility of string values
mesh_sampler_gen_out = [('x', 'O', None)]
lh_sampler_gen_out = [('x', float, None)]


class GridSampler(libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):
        self.nworkers = self._config.options.nworkers
        self.exact_mesh = self._config.options.software_options.mesh_file
        sampler_repeats = int(self._config.options.software_options.sampler_repeats)
        vectors = []

        # Named groups is a temporary construct to organize user-specified groups into separate lists.
        # Group labels can be thrown away after that.
        _named_groups = {}
        param_index = 0
        for code in self._config.codes:
            for param in code.parameters:
                vectors.append(param.create_array())
                if param.group:
                    _named_groups.setdefault(param.group, []).append(param_index)
                else:
                    _named_groups[uuid.uuid1()] = [param_index, ]
                param_index += 1
        groups = list(_named_groups.values())

        if self.exact_mesh:
            # Mesh should have shape (number of parameters, number of samples)
            mesh = np.load(self.exact_mesh)
            gen_out_dim = len(mesh)
            assert gen_out_dim == len(vectors), "Mesh file does not have the expected number of elements"
            sim_max = mesh.shape[1]
        else:
            sim_max = _total_scan_entries(vectors, groups)
            gen_out_dim = len(vectors)

        user_keys = {
            'vectors': vectors,
            'groups': groups,
            'exact_mesh': np.load(self.exact_mesh) if self.exact_mesh else None,
            'sampler_repeats': sampler_repeats
        }

        gen_out = [set_dtype_dimension(dtype, gen_out_dim) for dtype in mesh_sampler_gen_out]

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

        user_keys = {'gen_batch_size': self._config.options.software_options.batch_size,
                     'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds}

        gen_out = [set_dtype_dimension(dtype, len(self._config.lower_bounds)) for dtype in lh_sampler_gen_out]

        # for key, val in self._options.items():
        #     user_keys[key] = val

        self.gen_specs.update({'gen_f': latin_hypercube_sample,
                               'in': [],
                               'out': gen_out,
                               'user': user_keys})

        self.exit_criteria = {'sim_max': self._config.options.software_options.batch_size}

    def _configure_allocation(self):
        self.alloc_specs = {}

    def _configure_persistant_info(self):
        # _configure_specs must have been already called
        self.persis_info = add_unique_random_streams({}, self.nworkers + 1,
                                                     seed=self._config.options.software_options.seed)


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
                            'out': [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in
                                    restart_alloc_out]}

    def _configure_persistant_info(self):
        # No persis info needs to be maintained
        self.persis_info = {}

    def _set_evaluation_points(self):
        H_candidates = np.load(self.restart_from)
        H_new = tools.filter_completed_history(H_candidates)
        self.H0 = H_new
