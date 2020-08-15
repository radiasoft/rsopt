from libensemble.libE import libE
from rsopt.libe_tools.generator_functions.local_opt_generator import persistent_local_opt
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc
from libensemble.tools import add_unique_random_streams
from rsopt.optimizer import Optimizer
from rsopt.libe_tools.interface import get_local_optimizer_method
from rsopt.libe_tools.simulation_functions.python_simulation_functions import PythonFunction


# dimension for x needs to be set
persistent_local_opt_gen_out = [('x', float, None),
                                ('x_on_cube', float, None),
                                ('sim_id', int),
                                ('local_pt', bool)]

# Options like record interval are useful for a variety of optimizers and should not be mapped
#   to libE specific terms. Other libE specific options can retain their original terminology.
# FUTURE: Allowed option keys should be stored with parent once built out
LIBE_SPECS_ALLOWED = {'record_interval': 'save_every_k_sims'}


class libEnsembleOptimizer(Optimizer):
    # Configurationf or Local Optimization through uniform_or_localopt
    # Just sets up a local optimizer for now
    def __init__(self):
        super(libEnsembleOptimizer, self).__init__()
        self.libE_specs = {}

    def set_optimizer(self, method, options=None):
        self.optimizer_method = method
        for key in LIBE_SPECS_ALLOWED:
            if key in options:
                self.libE_specs[LIBE_SPECS_ALLOWED[key]] = options.pop[key]
        self.options = options

    def set_simulation(self, simulation, function=True):
        if function:
            self.function = simulation
        else:
            raise ValueError('Executable simulation not yet supported')

    def run(self):
        self._configure_libE()

        H, persis_info, flag = libE(self.sim_specs, self.gen_specs, self.exit_criteria, self.persis_info,
                                    self.alloc_specs, self.libE_specs)

        return H, persis_info, flag

    def _configure_optimizer(self):
        # TODO: The generator creation procedure needs to generalized and set up separately
        gen_out = [set_dtype_dimension(dtype, self.dimension) for dtype in persistent_local_opt_gen_out]
        user_keys = {'lb': self.lb,
                     'ub': self.ub,
                     'initial_sample_size': 1,
                     'xstart': self.start,
                     'localopt_method': get_local_optimizer_method(self.optimizer_method, 'nlopt')}
        print(user_keys['xstart'], type(user_keys['xstart']))
        for key, val in self.options.items():
            user_keys[key] = val
        gen_specs = {'gen_f': persistent_local_opt,
                     'in': [],
                     'out': gen_out,
                     'user': user_keys}
        self.gen_specs = gen_specs

    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs = {'alloc_f': persistent_aposmm_alloc, 'out': [('given_back', bool)],
                            'user': {}}

    def _configure_persistant_info(self):
        self.persis_info = add_unique_random_streams({}, self.nworkers + 1)

    def _configure_specs(self):
        # Persistent generator + local optimization eval = 2 workers always
        self.nworkers = 2
        self.comms = 'local'
        self.libE_specs = {'nworkers': self.nworkers, 'comms': self.comms, **self.libE_specs}

    def _configure_libE(self):
        self._set_dimension()
        self._configure_optimizer()
        self._configure_allocation()
        self._configure_specs()
        self._configure_persistant_info()
        self._configure_sim()

        if not self.exit_criteria:
            print('No libEnsemble exit criteria set. Optimizer will terminate when finished.')
            self.exit_criteria = {'sim_max': int(1e9)}

    def _configure_sim(self):
        # TODO: THe sim spec creation procedure needs to generalized and set up separately
        sim_function = PythonFunction(self.function, self.parameters, self.settings)
        self.sim_specs = {'sim_f': sim_function,
                          'in': ['x'],
                          'out': [('f', float), ]}

    def set_exit_criteria(self, exit_criteria):
        """
        Controls libEnsemble manage stopping point. This will override the optimizer if you have
        set tolerance or other stopping criteria for the optimization method.
        :param exit_criteria:
        :return:
        """
        options = ['sim_max', 'gen_max', 'elapsed_wallclock_time', 'stop_val']
        self.exit_criteria ={}
        for key, val in exit_criteria.items():
            if key in options:
                self.exit_criteria[key] = val
            else:
                raise KeyError(f'{key} is not a valid exit criteria option for libEnsemble')


def set_dtype_dimension(dtype, dimension):
    if len(dtype) == 2:
        return dtype
    elif len(dtype) == 3:
        new_dtype = (dtype[0], dtype[1], dimension)
        return new_dtype
    else:
        raise IndexError('size of dtype cannot be set')

