from libensemble.libE import libE
from rsopt.libe_tools.generator_functions.local_opt_generator import persistent_local_opt
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc
from libensemble.executors.mpi_executor import MPIExecutor
from rsopt.libe_tools.executors import SerialExecutor, register_rsmpi_executor
from libensemble.tools import add_unique_random_streams
from rsopt.optimizer import Optimizer, OPTIONS_ALLOWED
from rsopt.libe_tools.interface import get_local_optimizer_method
from rsopt.simulation import SimulationFunction


# dimension for x needs to be set
persistent_local_opt_gen_out = [('x', float, None),
                                ('x_on_cube', float, None),
                                ('sim_id', int),
                                ('local_pt', bool)]

# Options like record interval are useful for a variety of optimizers and should not be mapped
#   to libE specific terms. Other libE specific options can retain their original terminology.
# FUTURE: Allowed option keys should be stored with parent once built out
LIBE_SPECS_ALLOWED = {'record_interval': 'save_every_k_sims',
                      'use_worker_dirs': 'use_worker_dirs',
                      'working_directory': 'ensemble_dir_path'}
# These codes normally need separate working directories or input files will overwrite
_USE_WORKER_DIRS_DEFAULT = ['elegant', 'opal', 'python']
_LIBENSEMBLE_DIRECTORY = './ensemble'

def _configure_executor(job, name, executor):
    executor.register_calc(full_path=job.full_path, app_name=name, calc_type='sim')

def _set_app_names(config):
    codes = {}
    app_names = []
    for job in config.jobs:
        index = 1
        code = job.code
        if codes.get(code):
            index += codes[code]
        app_name = f'{code}_{index}'
        app_names.append(app_name)

        codes[code] = index

    return app_names



class libEnsembleOptimizer(Optimizer):
    # Configurationf or Local Optimization through uniform_or_localopt
    # Just sets up a local optimizer for now
    _NAME = 'libEnsemble'
    _SPECIFICATION_DICTS = ['gen_specs', 'libE_specs', 'sim_specs', 'alloc_specs']

    def __init__(self):
        super(libEnsembleOptimizer, self).__init__()
        self.options = []
        self.executor = None  # Set by method
        self.nworkers = 2  # Always 2 for local optimizer (1 for sim worker and 1 for persis generator)
        self.working_directory = _LIBENSEMBLE_DIRECTORY
        for spec in self._SPECIFICATION_DICTS:
            self.__setattr__(spec, {})

    def set_optimizer(self, software, method, objective_function=None, options=None):
        """
        Choose an optimizer and set supporting options.
        Optimizer package options are:
            nlopt
        Refer to individual package pages for a list of algorithms available.
        Options always available:
            record_interval (int): The history array from libEnsemble will be saved to file ever
                `record_interval` optimization steps.
            working_directory (str): Path to a directory where simulations will be run. Optimizer logs
                and records will still be created in the directory where the optimizer is run.
        :param software: (str) name of optimization package to use.
        :param method: (str) name of optimization algorithm.
        :param options: (dict) dictionary of options and settings.
        :return: None
        """

        # TODO: NEXT: This should just set method and options in the correct place in the Configuration
        #   there should be separate functions that load from the Configuration file when needed
        #   so it will not matter if setters are initiated from a python file or console loads a configuration file

        # move options to their appropriate dict for libE
        for key, mapping in OPTIONS_ALLOWED.items():
            if key in options:
                dict_name, dict_value = mapping[self._NAME]
                self.__getattribute__(dict_name)[dict_value] = options.pop(key)

        config_options = {'software': software, 'method': method,
                          'objective_function': objective_function, 'software_options': options}
        if not options.get('exit_criteria'):
            config_options['exit_criteria'] = {'sim_max': int(1000)}
        self._config.options = config_options

    def add_simulation(self, simulation, code):
        # TODO: documentation will need to be fleshed out when code types are set
        """
        Add a simulation of type `code` to the Jobs list. If code is 'python` then `simulation` should be a callable
        object that will run the simulation. Otherwise `simulation` should be the path to the
        run file for the simulation.

        Only serial simulations can be configured through the Python API. For parallel setup please use a YAML
        configuration file.

        Args:
            simulation: (callable or str) If code=='python` then simulation should be callable else should be string
            containing path (rel or abs) to run file.
            code: (str) Type of job to be run. See documentation for full set of options.

        Returns:
            None
        """
        self._manual_job_setup()
        if code == 'python':
            self._config.jobs[-1].setup = {'function': simulation,
                                          'execution_type': 'serial',
                                          'code': code}
        else:
            self._config.jobs[-1].setup = {'input_file': simulation,
                                           'execution_type': 'serial',
                                           'code': code}

    def run(self, clean_work_dir=False):
        self.clean_working_directory = clean_work_dir
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
                     'localopt_method': get_local_optimizer_method(self._config.method, 'nlopt'),
                     **self._config.options.software_options}

        for key, val in self._options.items():
            user_keys[key] = val
        self.gen_specs.update({'gen_f': persistent_local_opt,
                     'in': [],
                     'out': gen_out,
                     'user': user_keys})

    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': persistent_aposmm_alloc,
                                 'out': [('given_back', bool)],
                                 'user': {}})

    def _configure_persistant_info(self):
        self.persis_info = add_unique_random_streams({}, self.nworkers + 1)

    def _configure_specs(self):
        # Persistent generator + local optimization eval = 2 workers always
        self.comms = 'local'

        for job in self._config.jobs:
            if job.code in _USE_WORKER_DIRS_DEFAULT:
                # TODO: Move these checks into configuration
                self.libE_specs.setdefault('use_worker_dirs', True)
                self.libE_specs.setdefault('sim_dirs_make', True)


        self.libE_specs['sim_dir_symlink_files'] = self._config.get_sym_link_list()

        self.libE_specs.update({'nworkers': self.nworkers, 'comms': self.comms, **self.libE_specs})

    def _configure_sim(self):
        sim_function = SimulationFunction(self._config.jobs, self._config.options.get_objective_function())
        self.sim_specs.update({'sim_f': sim_function,
                               'in': ['x'],
                               'out': [('f', float), ]})

    def _configure_executor(self):
        app_names = _set_app_names(self._config)
        if self._config.options.executor_options:
            executor_setup = self._config.options.executor_options
        else:
            executor_setup = {'auto_resources': True}

        self.executor = self._config.create_exector(**executor_setup)

        # If the job has a run command then that job should use an executor
        for app_name, job in zip(app_names, self._config.jobs):
            if not job.full_path:
                pass
            else:
                _configure_executor(job, app_name, self.executor)
                job.executor = app_name

    def _configure_libE(self):
        self._set_dimension()
        self._configure_optimizer()
        self._configure_allocation()
        self._configure_specs()
        self._configure_persistant_info()
        self._configure_executor()
        self._configure_sim()
        self._cleanup()

        if self._config.options.exit_criteria:
            self.set_exit_criteria(self._config.options.exit_criteria)

        if not self.exit_criteria:
            print('No libEnsemble exit criteria set. Optimizer will terminate when finished.')
            self.exit_criteria = {'sim_max': int(1e9)}
        else:
            self._config.options.exit_criteria = self.exit_criteria

    def _cleanup(self):
        import shutil, os

        if self.clean_working_directory and os.path.isdir(self.working_directory):
            shutil.rmtree(self.working_directory)



    def set_exit_criteria(self, exit_criteria):
        """
        Controls libEnsemble manage stopping point. This will override the optimizer if you have
        set tolerance or other stopping criteria for the optimization method.
        :param exit_criteria:
        :return:
        """
        options = ['sim_max', 'gen_max', 'elapsed_wallclock_time', 'stop_val']
        self.exit_criteria = {}
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

