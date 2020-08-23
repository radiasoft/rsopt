from rsopt.configuration.parameters import _PARAMETER_READERS, Parameters
from rsopt.configuration.settings import _SETTING_READERS, Settings
from rsopt.configuration.setup import _SETUP_READERS, Setup


def get_reader(obj, category):
    config_categories = {'parameters': _PARAMETER_READERS,
                         'settings': _SETTING_READERS,
                         'setup': _SETUP_READERS}
    obj_type = type(obj)

    return config_categories[category][obj_type]


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
    """
    A Job encompasses a simulation to be run together with its pre and post processing options
    """
    def __init__(self, code):
        self.code = code

        self.parameters = Parameters()
        self.settings = Settings()
        self.setup = None
        self.pre_process = None
        self.post_process = None

        self.code_execution_type = None

    def set_parameters(self, parameters):
        reader = get_reader(parameters, 'parameters')
        for name, values in reader(parameters):
            self.parameters.parse(name, values)

    def set_settings(self, settings):
        reader = get_reader(settings, 'settings')
        for name, value in reader(settings):
            self.settings.parse(name, value)

    def set_setup(self, setup):
        reader = get_reader(setup, 'setup')
        self.setup = Setup.get_setup(setup, self.code)()
        for name, value in reader(setup):
            self.setup.parse(name, value)
