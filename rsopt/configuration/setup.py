

def read_setup_dict(input):
    for name, values in input.items():
        yield name, values


_SETUP_READERS = {
    dict: read_setup_dict
}


class Setup:
    __REQUIRED_KEYS = ('execution_type',)
    RUN_COMMAND = None

    def __init__(self):
        self.setup = {}

    @classmethod
    def get_setup(cls, setup):
        # verify execution type exists
        cls._check_setup(setup)
        execution_type = setup['execution_type']

        # verify requirements for given execution_type are met in setup
        setup_classes[execution_type]._check_setup(setup)

        return setup_classes[execution_type]

    @classmethod
    def _check_setup(cls, setup):
        for key in cls.__REQUIRED_KEYS:
            assert setup.get(key), f"{key} must be defined in setup"

    def parse(self, name, value):
         self.setup[name] = value


class Python(Setup):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = 'python'  # really translates to sys.executable

    @classmethod
    def get_run_command(cls, is_parallel):
        return cls.RUN_COMMAND


class Elegant(Setup):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = None
    SERIAL_RUN_COMMAND = 'elegant'
    PARALLEL_RUN_COMMAND = 'Pelgant'

    @classmethod
    def get_run_command(cls, is_parallel):
        if is_parallel:
            return cls.PARALLEL_RUN_COMMAND
        else:
            return cls.SERIAL_RUN_COMMAND


setup_classes = {
    'python': Python,
    'elegant': Elegant
}