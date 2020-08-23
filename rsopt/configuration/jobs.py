from rsopt.configuration import Settings, Parameters, Setup, get_reader

class Job:
    """
    A Job encompasses a simulation to be run together with its pre and post processing options
    """
    def __init__(self, code):
        self.parameters = Parameters()
        self.settings = Settings()
        self.setup = None
        self.pre_process = None
        self.post_process = None
        self.code = code

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
        self.setup = Setup.get_setup(setup)()
        for name, value in reader(setup):
            self.setup.parse(name, value)
