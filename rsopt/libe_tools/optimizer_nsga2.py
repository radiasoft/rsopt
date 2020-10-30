from rsopt.libe_tools import optimizer
from rsopt.libe_tools.interface import get_local_optimizer_method
from libensemble.gen_funcs.persistent_deap_nsga2 import deap_nsga2
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens

# TODO: make set_optimizer a member of Optimizer and have a Setup like class selection scheme
#  based on arguments of set_optimizer

# set_optimizer method: software is nsga2 and method does not need to be set currently

# dimension for individual set at run time
nsga2_gen_out =  [('individual', float, None), ('generation', int)]
_DEFAULT_WEIGHT = (-1.0, )

class EvolutionaryOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self):
        super().__init__()

        self.number_of_objectives = self._config.options.n_objectives

        self._generator_defaults = {
            # Set to DEAP implementation defaults
            'weights': _DEFAULT_WEIGHT * self.number_of_objectives,
            'pop_size': self.nworkers,
            'cxpb': 0.9,  # probability two individuals are crossed
            'eta': 20.0,  # large eta = low variation in children
            'indpb': 1.0 / self.number_of_objectives # Mutation probability
        }

    def _configure_optimizer(self):

        gen_out = [optimizer.set_dtype_dimension(dtype, self.dimension) for dtype in nsga2_gen_out]

        user_keys = {'lb': self.lb,
                     'ub': self.ub,
                     'pop_size': self.dimension,
                     **self._config.options.software_options}

        for key, val in self._generator_defaults.items():
            user_keys.setdefault(key, val)

        self.gen_specs.update({'gen_f': deap_nsga2,
                               'in': ['sim_id', 'generation', 'individual', 'fitness_values'],
                               'out': gen_out,
                               'user': user_keys})


    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': only_persistent_gens,
                                 'out': [('given_back', bool)]})

    def _configure_specs(self):
        self.comms = 'local'
        self.nworkers = self._config.options.nworkers
        for job in self._config.jobs:
            if job.code in optimizer._USE_WORKER_DIRS_DEFAULT:
                self.libE_specs.setdefault('use_worker_dirs', True)
                self.libE_specs.setdefault('sim_dirs_make', True)
                if job.code == 'python':
                    self.libE_specs.setdefault('sim_dir_symlink_files', [job.setup['input_file'],])
                break

        self.libE_specs.update({'nworkers': self.nworkers, 'comms': self.comms, **self.libE_specs})