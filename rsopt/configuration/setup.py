import os
import jinja2
from rsopt.codes import _TEMPLATED_CODES
from pykern import pkrunpy
from pykern import pkio
from pykern import pkresource

_PARALLEL_PYTHON_TEMPLATE = 'run_parallel_python.py.jinja'
_PARALLEL_PYTHON_RUN_FILE = 'run_parallel_python.py'
_TEMPLATE_PATH = pkio.py_path(pkresource.filename(''))

def read_setup_dict(input):
    for name, values in input.items():
        yield name, values


_SETUP_READERS = {
    dict: read_setup_dict
}

# Note to self: using classmethod for attributes that are set on a execution method basis and should never change
# can organize by class and call the classmethod to find the value
# Require keys is name mangled because technically any subclass should inherit the required
# keys of the parent. This is probably not the best way to do this though...


class Setup:
    __REQUIRED_KEYS = ('execution_type',)
    RUN_COMMAND = None
    NAME = None

    def __init__(self):
        self.setup = {
            'cores': 1
        }

    @classmethod
    def get_setup(cls, setup, code):
        # verify execution type exists
        cls._check_setup(setup)

        # TODO: rsmpi or mpi should change the run command
        execution_type = setup['execution_type']

        # verify requirements for given execution_type are met in setup
        setup_classes[code]._check_setup(setup)

        return setup_classes[code]

    @classmethod
    def _check_setup(cls, setup):
        for key in cls.__REQUIRED_KEYS:
            assert setup.get(key), f"{key} must be defined in setup"

    @classmethod
    def templated(cls):
        return cls.NAME in _TEMPLATED_CODES

    @classmethod
    def get_run_command(cls, is_parallel):
        return cls.RUN_COMMAND

    def generate_input_file(self, kwarg_dict, directory):
        # stub
        pass

    def parse(self, name, value):
         self.setup[name] = value


class Python(Setup):
    __REQUIRED_KEYS = ('function',)
    # SERIAL_RUN_COMMAND = 'python'  # really translates to sys.executable
    PARALLEL_RUN_COMMAND = 'python'
    NAME = 'python'

    @property
    def function(self):
        if self.setup.get('input_file'):
            module = pkrunpy.run_path_as_module(self.setup['input_file'])
            function = getattr(module, self.setup['function'])
            return function

        return self.setup['function']

    @classmethod
    def get_run_command(cls, is_parallel):
        if is_parallel:
            return cls.PARALLEL_RUN_COMMAND
        else:
            return None

    def generate_input_file(self, kwarg_dict, directory):
        assert self.setup.get('input_file'), "Input file must be provided to load Python function from"
        template_loader = jinja2.FileSystemLoader(searchpath=_TEMPLATE_PATH)
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template(_PARALLEL_PYTHON_TEMPLATE)

        output_template = template.render(dict_item=kwarg_dict, full_input_file_path=self.setup['input_file'],
                                          function=self.setup['function'])

        file_path = os.path.join(directory, _PARALLEL_PYTHON_RUN_FILE)

        with open(file_path, 'w') as ff:
            ff.write(output_template)


class Elegant(Setup):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = None
    SERIAL_RUN_COMMAND = 'elegant'
    PARALLEL_RUN_COMMAND = 'Pelgant'
    NAME = 'elegant'

    @classmethod
    def get_run_command(cls, is_parallel):
        if is_parallel:
            return cls.PARALLEL_RUN_COMMAND
        else:
            return cls.SERIAL_RUN_COMMAND


class Opal(Setup):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = 'opal'


class Genesis(Setup):
    __REQUIRED_KEYS = ('input_file', )
    SERIAL_RUN_COMMAND = 'genesis'
    PARALLEL_RUN_COMMAND = 'genesis_mpi'

    @classmethod
    def get_run_command(cls, is_parallel):
        if is_parallel:
            return cls.PARALLEL_RUN_COMMAND
        else:
            return cls.SERIAL_RUN_COMMAND


# This maybe should be linked to rsopt.codes._SUPPORTED_CODES,
# but is not expected to change often, so update manually for now
setup_classes = {
    'python': Python,
    'elegant': Elegant,
    'opal': Opal,
    'genesis': Genesis
}