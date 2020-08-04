from libensemble.libE import libE
from libensemble.gen_funcs.uniform_or_localopt import uniform_or_localopt
from libensemble.alloc_funcs.start_persistent_local_opt_gens import start_persistent_local_opt_gens
from libensemble.tools import add_unique_random_streams
from rsopt.optimizer import Optimizer
from rsopt.libe_tools.interface import get_local_optimizer_method

uniform_or_localopt_gen_out = [('priority', float),
                               ('local_pt', bool),
                               ('known_to_aposmm', bool),
                               ('dist_to_unit_bounds', float),
                               ('dist_to_better_l', float),
                               ('dist_to_better_s', float),
                               ('ind_of_better_l', int),
                               ('ind_of_better_s', int),
                               ('started_run', bool),
                               ('num_active_runs', int),
                               ('local_min', bool)]


class libEnsembleOptimizer(Optimizer):
    # Configurationf or Local Optimization through uniform_or_localopt
    def _set_dimension(self, array):
        self.dimension = array.size
        return self.dimension

    # Just sets up a local optimizer for now
    def set_optimizer(self, method, options=None):
        self.optimizer_method = method
        self.options = options

    def run(self):
        self._configure_libE()

        H, persis_info, flag = libE(sim_specs, self.gen_specs, self.exit_criteria, self.persis_info,
                                    self.alloc_specs, self.libE_specs)

        return H, persis_info, flag

    def _configure_optimizer(self):
        gen_out = uniform_or_localopt_gen_out + [('x', float, self.dimension), ('x_on_cube', float, self.dimension)]
        user_keys = {'lb': self.lb,
                     'ub': self.ub,
                     'localopt_method': get_local_optimizer_method(self.optimizer_method, 'nlopt')}
        gen_specs = {'gen_f': uniform_or_localopt,
                     'in': [],
                     'out': gen_out,
                     'user': user_keys}
        self.gen_specs = gen_specs

    def _configure_allocation(self, generator_out):
        # local optimizer allocation
        self.alloc_specs = {'alloc_f': start_persistent_local_opt_gens, 'out': generator_out,
                            'user': {'batch_mode': True, 'num_active_gens': 1}}

    def _configure_persistant_info(self):
        # TODO: self.nworkers must always be configured by this point
        self.persis_info = add_unique_random_streams({}, self.nworkers + 1)

    def _configure_specs(self):
        # Persistent generator + local optimization eval = 2 workers always
        self.nworkers = 2
        self.comms = 'local'
        self.libE_specs = {'nworkers': self.nworkers, 'comms': self.comms}

    def _configure_libE(self):
        self._configure_optimizer()
        self._configure_allocation(self.gen_specs['out'])
        self._configure_persistant_info()
        self._configure_specs()

        if not self.exit_criteria:
            print('No libEnsemble exit criteria set. Optimizer will terminate when finished.')
            self.exit_criteria = {'sim_max': int(1e9)}

    def set_exit_criteria(self, exit_criteria):
        """
        Controls libEnsemble manage stopping point. This will override the optimizer if you have
        set tolerance or other stopping criteria for the optimization method.
        :param exit_criteria:
        :return:
        """
        options = ['sim_max', 'gen_max', 'elapsed_wallclock_time', 'stop_val']

        for key, val in exit_criteria.items:
            if key in options:
                self.exit_criteria[key] = val
            else:
                raise KeyError(f'{key} is not a valid exit criteria option for libEnsemble')
