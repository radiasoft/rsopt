from libensemble.libE import libE
from rsopt.libe_tools.generator_functions.local_opt_generator import persistent_local_opt
from libensemble.alloc_funcs.persistent_aposmm_alloc import persistent_aposmm_alloc
from libensemble.tools import add_unique_random_streams
from rsopt.libe_tools import tools
from rsopt.libe_tools.interface import get_local_optimizer_method
from rsopt.simulation import SimulationFunction
from pykern import pkyaml
from rsopt import EXECUTOR_SCHEMA, OPTIMIZER_SCHEMA
import logging

logger = logging.getLogger('libensemble')
OPT_SCHEMA = pkyaml.load_file(OPTIMIZER_SCHEMA)
EXECUTOR_SCHEMA = pkyaml.load_file(EXECUTOR_SCHEMA)

# dtype dimensions > 1 are set at run time
persistent_local_opt_gen_out = [('x', float, None),
                                ('x_on_cube', float, None),
                                ('sim_id', int),
                                ('local_pt', bool)]

# Some libE_spec keys are re-mapped to rsopt terminology
LIBE_SPECS_ALLOWED = {'record_interval': 'save_every_k_sims',
                      'use_worker_dirs': 'use_worker_dirs',
                      'working_directory': 'ensemble_dir_path'}

def _configure_executor(job, name, executor):
    executor.register_app(full_path=job.full_path, app_name=name, calc_type='sim')


def _set_app_names(config):
    codes = {}
    app_names = []
    for code in config.codes:
        index = 1
        code = code.code
        if codes.get(code):
            index += codes[code]
        app_name = f'{code}_{index}'
        app_names.append(app_name)

        codes[code] = index

    return app_names


class libEnsembleOptimizer:
    # Configurationf or Local Optimization through uniform_or_localopt
    # Just sets up a local optimizer for now
    _NAME = 'libEnsemble'
    _OPT_SCHEMA = OPT_SCHEMA

    def __init__(self, config_model):
        self._config = config_model
        self.options = []
        self.H0 = None
        self.executor = None  # Set by method
        self.nworkers = 2  # Always 2 for local optimizer (1 for sim worker and 1 for persis generator)

        self.gen_specs = {}
        self.libE_specs = {}
        self.sim_specs = {}
        self.alloc_specs = {}
        self.exit_criteria = self._config.options.exit_criteria.model_dump()


    def run(self, clean_work_dir=False):
        self.clean_working_directory = clean_work_dir
        self._configure_libE()

        H, persis_info, flag = libE(self.sim_specs, self.gen_specs, self.exit_criteria, self.persis_info,
                                    self.alloc_specs, self.libE_specs, H0=self.H0)

        return H, persis_info, flag

    def _configure_optimizer(self):
        local_opt_method = get_local_optimizer_method(self._config.options.method.name,
                                                      self._config.options.software)
        gen_out = [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in persistent_local_opt_gen_out]
        user_keys = {'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds,
                     'initial_sample_size': 1,
                     'xstart': self._config.start,
                     'localopt_method': local_opt_method,
                     **self._config.options.software_options.model_dump()
                     }

        self.gen_specs.update({'gen_f': persistent_local_opt,
                               'persis_in': self._config.options.method.persis_in +
                                            [n[0] for n in gen_out],
                               'out': gen_out,
                               'user': user_keys})

    def _configure_allocation(self):
        # local optimizer allocation
        self.alloc_specs.update({'alloc_f': persistent_aposmm_alloc})

    def _configure_persistant_info(self):
        self.persis_info = add_unique_random_streams({}, self.nworkers + 1)

    def _configure_specs(self):
        # Persistent generator + local optimization eval = 2 workers always
        self.comms = 'local'

        # Directory structure setup
        self.libE_specs['sim_dirs_make'] = True
        self.libE_specs['use_worker_dirs'] = self._config.options.use_worker_dirs
        self.libE_specs['ensemble_dir_path'] = self._config.options.run_dir

        # Files needed for each simulation
        self.libE_specs['sim_dir_symlink_files'] = self._config.get_sym_link_list()
        if self._config.options.record_interval:
            self.libE_specs['save_every_k_sims'] = self._config.options.record_interval

        self.libE_specs.update({'nworkers': self.nworkers, 'comms': self._config.comms, **self.libE_specs})
        if self._config.mpi_comm:
            self.libE_specs['mpi_comm'] = self._config.mpi_comm

        self.libE_specs['dedicated_mode'] = True  # This used to be called 'central_mode' and was set in Executor
        self.libE_specs['disable_resource_manager'] = False  # This used to be called 'auto_resources and was set in Executor

        # If no executor is used libEnsemble will raise an error for calculation of task_timing
        if any([c.use_executor for c in self._config.codes]):
            executor_timings = True
        else:
            executor_timings = False
        self.libE_specs['stats_fmt'] = {'task_timing': executor_timings,
                                        'task_datetime': executor_timings
                                        }

        if self._config.rsmpi_executor:
            self.libE_specs['resource_info'] = {'cores_on_node':
                                                    (EXECUTOR_SCHEMA['rsmpi']['cores_on_node']['physical_cores'],
                                                     EXECUTOR_SCHEMA['rsmpi']['cores_on_node']['logical_cores']),
                                                'node_file': EXECUTOR_SCHEMA['rsmpi']['node_file']}

        if self._config.options.use_zero_resources:
            # Do not assign resources to the generator
            self.libE_specs['zero_resource_workers'] = [1]

    def _configure_sim(self):
        sim_function = SimulationFunction(self._config.codes, self._config.options.objective_function)
        self.sim_specs.update(
            {
                'sim_f': sim_function,
                'inputs': self._config.options.method.sim_specs.inputs,
                'outputs': self._config.options.method.sim_specs.outputs,
            }
        )

    def _configure_executors(self):
        app_names = _set_app_names(self._config)

        # If the job has a run command then that job should use an executor
        for app_name, job in zip(app_names, self._config.codes):
            if not job.use_executor:
                pass
            else:
                if not self.executor:
                    self._create_executor()
                _configure_executor(job, app_name, self.executor)
                job.executor = app_name
                job.executor_args['app_name'] = app_name

    def _create_executor(self):
        self.executor = self._config.create_exector()

    def _configure_libE(self):
        self._configure_optimizer()
        self._configure_allocation()
        self._configure_specs()
        self._configure_persistant_info()
        self._configure_executors()
        self._configure_sim()
        self._cleanup()

    def _cleanup(self):
        import shutil, os

        if self.clean_working_directory and os.path.isdir(self._config.options.run_dir):
            shutil.rmtree(self._config.options.run_dir)
