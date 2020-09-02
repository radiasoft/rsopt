from rsopt.configuration.parameters import _PARAMETER_READERS, Parameters
from rsopt.configuration.settings import _SETTING_READERS, Settings
from rsopt.configuration.setup import _SETUP_READERS, Setup


def get_reader(obj, category):
    config_categories = {'parameters': _PARAMETER_READERS,
                         'settings': _SETTING_READERS,
                         'setup': _SETUP_READERS}
    reader_options = config_categories[category]
    for key, value in reader_options.items():
        if isinstance(obj, key):
            return value

    raise TypeError(f'{category} input type is not recognized')


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
        self.pre_process = None
        self.post_process = None

        self.code_execution_type = None

    @property
    def parameters(self):
        return self._parameters.pararameters
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
        assert setup.get('code'), "Code must be specified in the setup dictionary"
        if not self.code:
            self.code = setup.get('code')
        assert self.code, "A code must be set before adding a setup to a Job"

        reader = get_reader(setup, 'setup')
        self._setup = Setup.get_setup(setup, self.code)()
        for name, value in reader(setup):
            self._setup.parse(name, value)
