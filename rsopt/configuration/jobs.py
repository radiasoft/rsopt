from rsopt.configuration.parameters import _PARAMETER_READERS, Parameters
from rsopt.configuration.settings import _SETTING_READERS, Settings
from rsopt.configuration.setup import _SETUP_READERS, Setup, _PARALLEL_PYTHON_RUN_FILE


def get_reader(obj, category):
    config_categories = {'parameters': _PARAMETER_READERS,
                         'settings': _SETTING_READERS,
                         'setup': _SETUP_READERS}
    reader_options = config_categories[category]
    for key, value in reader_options.items():
        if isinstance(obj, key):
            return value

    raise TypeError(f'{category} input type is not recognized')


def create_executor_arguments(setup):
    # Really creates Executor.submit() arguments
    args = {
        'num_procs': setup.get('cores', 1),
        'num_nodes': None,  # No user interface right now
        'ranks_per_node': None, # No user interface right now
        'machinefile': None,  # Add in  setup.machinefile if user wants to control
        'app_args': setup.get('input_file', None),
        'hyperthreads': False,  # Add in  setup.hyperthreads if this is needed
        # 'app_name': None,  # Handled at optimizer setup
        # 'stdout': None,  # Handled at optimizer setup
        # 'stderr': None, # Handled at optimizer setup
        # 'stage_inout': None,  # No used
        # 'dry_run': False, # Keep false for now
        # 'extra_args': None  # Unused
    }

    for key, value in args.items():
        args[key] = setup.get(key, value)

    # Cannot be overridden
    args['calc_type'] = 'sim'
    args['wait_on_run'] = True

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
    def parameters(self):
        return self._parameters.parameters
    @property
    def settings(self):
        return self._settings.settings
    @property
    def setup(self):
        if self._setup:
            return self._setup.setup
        else:
            return None
    @property
    def execute(self):
        return self._setup.function

    @property
    def input_distribution(self):
        # Used by conversion: a Switchyard will write a file called 'input_distribution' for the job to use
        return self._setup.setup.get('input_distribution')

    @property
    def output_distribution(self):
        # Used by conversion: a Switchyard will read file called 'output_distribution' for a future job to use
        return self._setup.setup.get('output_distribution')

    @property
    def pre_process(self):
        return self._setup.setup.get('preprocess')

    @property
    def post_process(self):
        return self._setup.setup.get('postprocess')

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
        is_parallel = self.setup.get('cores', 1) > 1
        self.full_path = self._setup.get_run_command(is_parallel=is_parallel)
        self.executor_args = create_executor_arguments(self._setup.setup)

        # TODO: This might be better generalized by creating an option to supply app_args
        if is_parallel and self.code == 'python':
            self.executor_args['app_args'] = _PARALLEL_PYTHON_RUN_FILE

        # Import input_file
        if self._setup.setup.get('input_file'):
            self._setup.input_file_model = self._setup.parse_input_file(self._setup.setup.get('input_file'),
                                                                        self.setup.get('execution_type', False) == 'shifter')
