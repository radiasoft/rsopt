from rsopt.configuration.parameters import PARAMETER_READERS, Parameters
from rsopt.configuration.settings import SETTING_READERS, Settings
from rsopt.configuration.setup import SETUP_READERS
from rsopt.configuration.setup.python import _PARALLEL_PYTHON_RUN_FILE
from rsopt.configuration.setup.setup import Setup
import typing

_USE_SIM_DIRS_DEFAULT = ['elegant', 'opal', 'genesis']


def get_reader(obj, category):
    config_categories = {'parameters': PARAMETER_READERS,
                         'settings': SETTING_READERS,
                         'setup': SETUP_READERS}
    reader_options = config_categories[category]
    for key, value in reader_options.items():
        if isinstance(obj, key):
            return value

    raise TypeError(f'{category} input type is not recognized')


def create_executor_arguments(setup: Setup, is_parallel: bool) -> dict:
    # Really creates Executor.submit() arguments
    args = {
        'num_procs': setup.setup.get('cores', 1),
        'num_nodes': None,  # No user interface right now
        'procs_per_node': None, # No user interface right now
        'machinefile': None,  # Add in  setup.machinefile if user wants to control
        'app_args': setup.format_task_string(is_parallel),
        'hyperthreads': False,  # Add in  setup.hyperthreads if this is needed
        'wait_on_start': True,
        # 'app_name': None,  # Handled at optimizer setup
        # 'stdout': None,  # Handled at optimizer setup
        # 'stderr': None, # Handled at optimizer setup
        # 'stage_inout': None,  # Not used in rsopt
        # 'dry_run': False, # No support for dry runs in rsopt
        # TODO: This should only be used for openmpi
        'extra_args': "--bind-to none" # args go to MPI runner command directly
    }

    # TODO: Should there really be this kind of hidden interface to override executor setup?
    # for key, value in args.items():
    #     args[key] = setup.setup.get(key, value)

    # Cannot be overridden
    args['calc_type'] = 'sim'
    args['wait_on_start'] = True

    return args


class Job:
    # Job should never assume any particular code so that all parts may be set independently
    # When actually executed, or setting up to execute, then setup is queried to decide execution
    """
    A Job encompasses a simulation to be run together with its pre and post processing options
    """
    def __init__(self, code=None):
        self.code = code

        self._parameters = Parameters()
        self._settings = Settings()
        self._setup = None
        self.full_path = None

        self.executor = None  # Name of the executor registered with libEnsemble
        self.executor_args = {}  # Arguments configured by Job for the libEnsemble Executor.submit

    @property
    def parameters(self) -> dict:
        return self._parameters.parameters

    @property
    def settings(self) -> dict:
        return self._settings.settings

    @property
    def setup(self) -> dict or None:
        if self._setup:
            return self._setup.setup
        else:
            return None

    @property
    def execute(self):
        return self._setup.function

    @property
    def is_parallel(self) -> bool:
        # parser will have already guaranteed that execution_type exists and is a valid value
        return ((self.setup.get('cores', 1) > 1) & (self.setup.get('execution_type') != 'serial')) or \
                            self.setup.get('force_executor', False)

    @property
    def input_distribution(self):
        # Used by conversion: a Switchyard will write a file called 'input_distribution' for the job to use
        return self._setup.setup.get('input_distribution')

    @property
    def output_distribution(self):
        # Used by conversion: a Switchyard will read file called 'output_distribution' for a future job to use
        return self._setup.setup.get('output_distribution')

    @property
    def pre_process(self) -> callable:
        # Iterator that returns any preprocess functions defined in setup
        for pre in self._setup.preprocess:
            yield pre

    @property
    def post_process(self) -> callable:
        # Iterator that returns any postprocess functions defined in setup
        for post in self._setup.postprocess:
            yield post

    @property
    def timeout(self):
        timeout = self._setup.setup.get('timeout') or 1e10
        return timeout

    @property
    def sim_dirs_required(self) -> bool:
        if self.code in _USE_SIM_DIRS_DEFAULT or (self.code == 'python' and self.setup['cores'] > 1):
            return True
        return False

    @property
    def sym_link_targets(self) -> set:
        return self._setup.get_sym_link_targets()

    def get_ignored_files(self, with_path: bool = False) -> typing.List[str]:
        """Get files that should be ignored by sirepo.lib parse.

        Args:
            with_path: If with_path then prepend the path from input_file, if any.

        Returns: list

        """

        ignored_files = self._setup.get_ignored_files
        if self.input_distribution:
            ignored_files.append(self.input_distribution)

        if with_path and ignored_files:
            ignored_files = [str(self._setup.input_file_path.joinpath(f)) for f in ignored_files]

        return ignored_files

    @parameters.setter
    def parameters(self, parameters):
        reader = get_reader(parameters, 'parameters')
        for name, values in reader(parameters):
            self._parameters.parse(name, values)

    @settings.setter
    def settings(self, settings):
        reader = get_reader(settings, 'settings')
        for name, value in reader(settings):
            self._settings.parse(name, value)

    @setup.setter
    def setup(self, setup):
        # `code` must be set here if not set at Job instantiation,
        # but this method cannot override `code` if it was set at instantiation of the job
        if not self.code:
            assert setup.get('code'), "Code not specified during setup instantiation" \
                                      "Code must be included in the setup dictionary"
            self.code = setup.get('code')
        assert self.code, "A code must be set before adding a setup to a Job"

        reader = get_reader(setup, 'setup')
        self._setup = Setup.get_setup(setup, self.code)()
        for name, value in reader(setup):
            self._setup.parse(name, value)

        # Setup for Executor
        if self.setup.get('force_executor') and not self.setup.get('cores'):
            self.setup['cores'] = 1

        if (not self.is_parallel) & (self.setup.get('cores', 1) > 1):
            print('Warning! serial execution requested with more than 1 core. Serial execution will be used.')
        self.full_path = self._setup.get_run_command(is_parallel=self.is_parallel)
        self.executor_args = create_executor_arguments(self._setup, self.is_parallel)

        if self.is_parallel and self.code == 'python':
            self.executor_args['app_args'] = _PARALLEL_PYTHON_RUN_FILE

        # Import input_file
        if self._setup.setup.get('input_file'):
            self._setup.input_file_model = self._setup.parse_input_file(self._setup.setup.get('input_file'),
                                                                        self.setup.get('execution_type', False) == 'shifter',
                                                                        self.get_ignored_files())
