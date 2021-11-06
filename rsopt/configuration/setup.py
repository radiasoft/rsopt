import os
import sys
import jinja2
import pickle
from rsopt import util
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
_SHIFTER_SIREPO_SCRIPT = pkio.py_path(pkresource.filename('shifter_sirepo.py'))
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
            commands[c['_type'].lower()] = [i]
        else:
            commands[c['_type'].lower()].append(i)
    for i, e in enumerate(model.models.elements):
        elements[e['name'].upper()] = [i]

    return commands, elements


def _validate_execution_type(key):
    if key in _EXECUTION_TYPES:
        return True
    else:
        return False


def _shifter_parse_model(name, input_file):
    import shlex
    from subprocess import Popen, PIPE

    node_to_use = util.return_unused_node()
    if node_to_use:
        run_string = f"srun -w {node_to_use} --ntasks 1 --nodes 1 shifter --image={_SHIFTER_IMAGE} " \
                     f"/bin/bash {_SHIFTER_BASH_FILE} python {_SHIFTER_SIREPO_SCRIPT}"
        run_string = ' '.join([run_string, name, input_file])
        cmd = Popen(shlex.split(run_string), stderr=PIPE, stdout=PIPE)
        out, err = cmd.communicate()
        if err:
            print(err.decode())
            raise Exception('Model load from Sirepo in Shifter failed.')
        d = pickle.loads(out)
    else:
        d = None

    return util.broadcast(d)


_SETUP_READERS = {
    dict: read_setup_dict
}


def _create_sym_links(*args, link_location='default'):
    for filepath in args:
        if link_location == 'default':
            filename = os.path.split(filepath)[-1]
        else:
            filename = link_location
        os.symlink(filepath, filename)


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
        self.handlers = {'preprocess': self._handle_preprocess,
                         'postprocess': self._handle_preprocess}
        self._preprocess = []
        self._postprocess = []

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
    def parse_input_file(cls, input_file, shifter):

        if shifter:
            d = _shifter_parse_model(cls.NAME, input_file)
        else:
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
        self.process_input(name, value)
        self.setup[name] = value

    def validate_input(self, key, value):
        # Checks inputs with controlled inputs
        if self.validators.get(key):
            if self.validators[key](value):
                return
            else:
                raise ValueError(f'{value} is not a recognized value for f{key}')

    def process_input(self, key, value):
        # Handling for special inputs
        if self.handlers.get(key):
            return self.handlers[key](value)
        else:
            return value

    def get_run_command(self, is_parallel):
        # There is an argument for making this a method of the Job class
        # if it continues to grow in complexity it is worth moving out to a higher level
        # class that has more information about the run configuration
        if is_parallel:
            run_command = self.PARALLEL_RUN_COMMAND
        else:
            run_command = self.SERIAL_RUN_COMMAND

        if self.setup.get('execution_type') == 'shifter':
            run_command = ' '.join([self.SHIFTER_COMMAND, run_command])

        return run_command

    def _handle_preprocess(self, value):
        # Run in the rsopt calling directory, not worker directories
        module_path, function_name = value
        module = pkrunpy.run_path_as_module(module_path)
        function = getattr(module, function_name)
        self._preprocess.append(function)
        return True

    def _handle_postprocess(self, value):
        # Run in the rsopt calling directory, not worker directories
        module_path, function_name = value
        module = pkrunpy.run_path_as_module(module_path)
        function = getattr(module, function_name)
        self._postprocess.append(function)
        return True


class Python(Setup):
    __REQUIRED_KEYS = ('function',)
    SERIAL_RUN_COMMAND = None  # serial not executed by subprocess so no run command is needed
    PARALLEL_RUN_COMMAND = 'python'
    NAME = 'python'

    @property
    def function(self):
        if self.setup.get('input_file'):
            # libEnsemble workers change active directory - sys.path will not record locally available modules
            sys.path.append('.')

            module = pkrunpy.run_path_as_module(self.setup['input_file'])
            function = getattr(module, self.setup['function'])
            return function

        return self.setup['function']

    @classmethod
    def parse_input_file(cls, input_file, shifter):
        # Python does not use text input files. Functions are dynamically imported by `function`.
        return None

    def generate_input_file(self, kwarg_dict, directory):
        is_parallel = self.setup.get('execution_type', False) == 'parallel' or self.setup.get('execution_type',
                                                                                              False) == 'rsmpi'
        if not is_parallel:
            return None

        assert self.setup.get('input_file'), "Input file must be provided to load Python function from"
        template_loader = jinja2.FileSystemLoader(searchpath=_TEMPLATE_PATH)
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template(_PARALLEL_PYTHON_TEMPLATE)

        dict_item_str = {}
        for k, v in kwarg_dict.items():
            if type(v) == str:
                dict_item_str[k] = v
        for k in dict_item_str.keys():
            kwarg_dict.pop(k)

        output_template = template.render(dict_item=kwarg_dict, dict_item_str=dict_item_str, full_input_file_path=self.setup['input_file'],
                                          function=self.setup['function'])

        file_path = os.path.join(directory, _PARALLEL_PYTHON_RUN_FILE)

        with open(file_path, 'w') as ff:
            ff.write(output_template)

    def get_run_command(self, is_parallel):
        # Python has no serial run command. Force the parallel run mode if using shifter.
        if is_parallel:
            run_command = self.PARALLEL_RUN_COMMAND
        else:
            run_command = self.SERIAL_RUN_COMMAND

        if self.setup.get('execution_type') == 'shifter':
            run_command = ' '.join([self.SHIFTER_COMMAND, self.PARALLEL_RUN_COMMAND])

        return run_command


class Elegant(Setup):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = None
    SERIAL_RUN_COMMAND = 'elegant'
    PARALLEL_RUN_COMMAND = 'Pelegant'
    NAME = 'elegant'

    def _edit_input_file_schema(self, kwarg_dict):
        # Name cases in the Sirepo model:
        # eLeMENt NAmeS
        # ELEMENT TYPES
        # element parameters
        # command _type
        # command parameters

        # While exact element name case is kept at model read all elements are written to upper case. I think elegant
        # doesn't distinguish case anyway. For the element parser we'll assume element names are unique regardless of
        # case.

        commands, elements = _get_model_fields(self.input_file_model)  # modifies element name case to UPPER
        model = deepcopy(self.input_file_model)

        for n, v in kwarg_dict.items():
            field, index, name = _parse_name(n)

            if field.lower() in commands.keys():
                assert index or len(commands[field.lower()]) == 1, \
                    "{} is not unique in {}. Please add identifier".format(n, self.setup['input_file'])
                id = commands[field.lower()][int(index) - 1 if index else 0]
                model.models.commands[id][name.lower()] = v
            elif field.upper() in elements:  # Sirepo maintains element name case so we standardize to upper here
                id = elements[field.upper()][0]
                if model.models.elements[id].get(name.lower()) is not None:
                    model.models.elements[id][name.lower()] = v
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


class Opal(Elegant):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = 'opal'
    SERIAL_RUN_COMMAND = 'opal'
    PARALLEL_RUN_COMMAND = 'opal'
    NAME = 'opal'


class User(Python):
    __REQUIRED_KEYS = ('input_file', 'run_command', 'file_mapping', 'file_definitions')
    NAME = 'user'

    def __init__(self):
        super().__init__()
        self._BASE_RUN_PATH = pkio.py_path()

    def get_run_command(self, is_parallel):
        # run_command is provided by user so no check for serial or parallel run mode
        run_command = self.setup['run_command']

        # Hardcode genesis input syntax: 'genesis < input_file.txt'
        if run_command.strip() in ['genesis', 'genesis_mpi']:
            run_command = ' '.join([run_command, '<'])

        if self.setup.get('execution_type') == 'shifter':
            run_command = ' '.join([self.SHIFTER_COMMAND, run_command])

        return run_command

    def get_file_def_module(self):

        module_path = os.path.join(self._BASE_RUN_PATH, self.setup['file_definitions'])
        module = pkrunpy.run_path_as_module(module_path)
        return module

    def generate_input_file(self, kwarg_dict, directory):

        # Get strings for each file and fill in arguments for this job
        for key, val in self.setup['file_mapping'].items():
            local_file_instance = self.get_file_def_module().__getattribute__(key).format(**kwarg_dict)
            pkio.write_text(os.path.join(directory, val), local_file_instance)


class Genesis(Elegant):
    __REQUIRED_KEYS = ('input_file',)
    NAME = 'genesis'
    SERIAL_RUN_COMMAND = 'genesis'
    PARALLEL_RUN_COMMAND = 'genesis_mpi'

    @classmethod
    def parse_input_file(cls, input_file, shifter):
        # assumes lume-genesis can best installed locally - shifter execution not needed
        # expand_paths is not used to ensure that generated input files are used if desired - otherwise rsopt symlinks them to run dir
        import genesis
        d = genesis.Genesis(input_file, use_tempdir=False, expand_paths=False, check_executable=False)

        return d

    def _edit_input_file_schema(self, kwarg_dict):
        # Name cases:
        # All lower for lume-genesis
        param, elements = self.input_file_model.param, self.input_file_model.lattice['eles']
        model = deepcopy(self.input_file_model)

        for name, value in kwarg_dict.items():

            name = name.lower()  # lume-genesis makes all names lowercase
            if name in param.keys():
                model.param[name] = value
            else:
                raise ValueError("`{}` was not found in loaded input files".format(name))

        return model

    def generate_input_file(self, kwarg_dict, directory):
        model = self._edit_input_file_schema(kwarg_dict)
        model.configure_genesis(workdir='.')

        model.write_input_file()
        model.write_beam()
        model.write_lattice()

        # rad and dist files are not written by lume-genesis so we symlink them in if they exist in start directory
        for filename in [model['distfile'], model['radfile']]:
            full_path = os.path.join(model.original_path, filename)
            if os.path.isfile(full_path):
                _create_sym_links(os.path.relpath(full_path))

        # lume-genesis hard codes the input file name it write to as "genesis.in"
        os.rename('genesis.in', self.setup['input_file'])


# This maybe should be linked to rsopt.codes._SUPPORTED_CODES,
# but is not expected to change often, so update manually for now
setup_classes = {
    'python': Python,
    'elegant': Elegant,
    'opal': Opal,
    'user': User,
    'genesis': Genesis
}