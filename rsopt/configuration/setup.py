import os
import jinja2
from rsopt.codes import _TEMPLATED_CODES
from copy import deepcopy
from pykern import pkrunpy
from pykern import pkio
from pykern import pkresource
from libensemble.executors.mpi_executor import MPIExecutor
from rsopt.libe_tools.executors import register_rsmpi_executor


_PARALLEL_PYTHON_TEMPLATE = 'run_parallel_python.py.jinja'
_PARALLEL_PYTHON_RUN_FILE = 'run_parallel_python.py'
_TEMPLATE_PATH = pkio.py_path(pkresource.filename(''))
_SHIFTER_BASH_FILE = pkio.py_path(pkresource.filename('shifter_exec.sh'))
_SHIFTER_IMAGE = 'radiasoft/sirepo:prod'
_EXECUTION_TYPES = {'serial': MPIExecutor,  # Serial jobs executed in the shell use the MPIExecutor for simplicity
                    'parallel': MPIExecutor,
                    'rsmpi': register_rsmpi_executor,
                    'shifter': MPIExecutor}


def read_setup_dict(input):
    for name, values in input.items():
        yield name, values


def _parse_name(name):
    components = name.split('.')
    if len(components) == 3:
        field, index, name = components
    elif len(components) == 2:
        field, index, name = components[0], None, components[1]
    else:
        raise ValueError(f'Could not understand parameter/setting name {name}')

    return field, index, name


def _get_model_fields(model):
    commands = {}
    command_types = []
    elements = {}
    for i, c in enumerate(model.models.commands):
        if c['_type'] not in command_types:
            command_types.append(c['_type'])
            commands[c['_type']] = [i]
        else:
            commands[c['_type']].append(i)
    for i, e in enumerate(model.models.elements):
        elements[e['name']] = [i]

    return commands, elements


def _validate_execution_type(key):
    if key in _EXECUTION_TYPES:
        return True
    else:
        return False

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
    SHIFTER_COMMAND = f'shifter --image={_SHIFTER_IMAGE} /bin/bash {_SHIFTER_BASH_FILE}'

    def __init__(self):
        self.setup = {
            'cores': 1
        }
        self.input_file_model = None
        self.validators = {'execution_type': _validate_execution_type}

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
    def parse_input_file(cls, input_file):
        # Prevent Sirepo from being required for default install
        # TODO: This could possibly be returned to a top level import if setup.py is split out by code
        import sirepo.lib
        d = sirepo.lib.Importer(cls.NAME).parse_file(input_file)

        return d

    def generate_input_file(self, kwarg_dict, directory):
        # stub
        pass

    def _edit_input_file_schema(self, kwargs):
        # stub
        pass

    def parse(self, name, value):
        self.validate_input(name, value)
        self.setup[name] = value

    def validate_input(self, key, value):
        # Checks inputs with controlled inputs
        if self.validators.get(key):
            if self.validators[key](value):
                return
            else:
                raise ValueError(f'{value} is not a recognized value for f{key}')

    def get_run_command(self, is_parallel):
        # There is an argument for making this a method of the Job class
        # if it continues to grow in complexity it is worth moving out to a higher level
        # class that has more information about the run configuration
        if is_parallel:
            run_command =  self.PARALLEL_RUN_COMMAND
        else:
            run_command = self.SERIAL_RUN_COMMAND

        if self.setup.get('execution_type') == 'shifter':
            run_command = ' '.join([self.SHIFTER_COMMAND, run_command])

        return run_command


class Python(Setup):
    __REQUIRED_KEYS = ('function',)
    SERIAL_RUN_COMMAND = None  # serial not executed by subprocess so no run command is needed
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
    def parse_input_file(cls, input_file):
        # Python does not use text input files. Functions are dynamically imported by `function`.
        return None

    def generate_input_file(self, kwarg_dict, directory):
        is_parallel =  self.setup.get('execution_type', False) == 'parallel' or self.setup.get('execution_type', False) == 'rsmpi'
        if not is_parallel:
            return None

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
    PARALLEL_RUN_COMMAND = 'Pelegant'
    NAME = 'elegant'

    def _edit_input_file_schema(self, kwarg_dict):
        # Name cases:
        # ELEMENT NAMES
        # ELEMENT TYPES
        # element parameters
        # command _type
        # command parameters

        commands, elements = _get_model_fields(self.input_file_model)
        model = deepcopy(self.input_file_model)

        for n, v in kwarg_dict.items():
            field, index, name = _parse_name(n)
            name = name.lower()  # element/command parameters are always lower
            if field.lower() in commands.keys():
                assert index or len(commands[field.lower()]) == 1, \
                    "{} is not unique in {}. Please add identifier".format(n, self.setup['input_file'])
                id = commands[field.lower()][int(index)-1 if index else 0]
                model.models.commands[id][name] = v
            elif field.upper() in elements:
                id = elements[field][0]
                if model.models.elements[id].get(name) is not None:
                    model.models.elements[id][name] = v
                else:
                    ele_type = model.models.elements[id]["type"]
                    ele_name = model.models.elements[id]["name"]
                    raise NameError(f"Parameter: {name} is not found for element {ele_name} with type {ele_type}")
            else:
                raise ValueError("{} was not found in loaded .ele or .lte files".format(n))

        return model

    def generate_input_file(self, kwarg_dict, directory):
        model = self._edit_input_file_schema(kwarg_dict)

        model.write_files(directory)


class Opal(Setup):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = 'opal'


class Genesis(Setup):
    __REQUIRED_KEYS = ('input_file', )
    SERIAL_RUN_COMMAND = 'genesis'
    PARALLEL_RUN_COMMAND = 'genesis_mpi'



# This maybe should be linked to rsopt.codes._SUPPORTED_CODES,
# but is not expected to change often, so update manually for now
setup_classes = {
    'python': Python,
    'elegant': Elegant,
    'opal': Opal,
    'genesis': Genesis
}