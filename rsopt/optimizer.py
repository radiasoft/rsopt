from rsopt.configuration import Settings, Parameters, get_reader

_NAME = None

OPTIONS_ALLOWED = {'record_interval': {'libensemble': 'save_every_k_sims'},
                   'working_directory': {'libensemble': 'ensemble_dir_path'}
                   }

def _set_options(options):
    for option, value in options:
        if option in OPTIONS_ALLOWED:
            self._options[]

class Optimizer:
    name = _NAME

    def __init__(self):
        self.gen_specs = {}
        self.dimension = 0
        self.optimizer_method = ''
        self._options = {}
        self.settings = Settings()
        self.parameters = Parameters()

        self.recording_method = None
        self.exit_criteria = None
        self.function = None
        self.executable = None

    def _set_options(self, options):
        for option, value in options:
            option_name = OPTIONS_ALLOWED[option][self.name] if self.name else option
            self._options[option_name] = value

    @property
    def lb(self):
        return self.parameters.get_lower_bound()

    @lb.setter
    def lb(self, value=None):
        pass

    @property
    def ub(self):
        return self.parameters.get_upper_bound()

    @ub.setter
    def ub(self, value=None):
        pass

    @property
    def start(self):
        return self.parameters.get_start()

    @start.setter
    def start(self, value=None):
        pass

    def _set_dimension(self):
        if len(self.parameters.pararameters) == 0:
            print("Warning: Cannot set dimension. No parameters have been set.")
        else:
            self.dimension = len(self.parameters.pararameters)

    def set_parameters(self, parameters):
        reader = get_reader(parameters, 'parameters')
        for name, values in reader(parameters):
            self.parameters.parse_parameters(name, values)

    def set_settings(self, settings):
        reader = get_reader(settings, 'settings')
        for name, value in reader(settings):
            self.settings.parse_settings(name, value)

    def set_exit_criteria(self, exit_criteria):
        # TODO: Will override in sublcasses probably
        self.exit_criteria = exit_criteria

    def _set_recording(self):
        if self.recording_method:
            self.recording_method()
