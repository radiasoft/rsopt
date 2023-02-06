import abc
import pathlib
import pickle
import shutil
import typing
from rsopt import util
from rsopt.codes import TEMPLATED_CODES
from rsopt import SETUP_SCHEMA
from pykern import pkrunpy
from pykern import pkio
from pykern import pkresource
from pykern import pkyaml

from rsopt.configuration.setup import EXECUTION_TYPES

_SHIFTER_BASH_FILE = pkio.py_path(pkresource.filename('shifter_exec.sh'))
_SHIFTER_SIREPO_SCRIPT = pkio.py_path(pkresource.filename('shifter_sirepo.py'))
_DEFAULT_SHIFTER_IMAGE = 'radiasoft/sirepo:prod'


def _validate_execution_type(key: str) -> bool:
    if key in EXECUTION_TYPES:
        return True
    else:
        return False


def _shifter_parse_model(name: str, input_file: str, ignored_files: list) -> typing.Type['sirepo.lib.SimData'] or None:
    # Sidesteps the difficulty of Sirepo install on NERSC by running a script that parses to the Sirepo model
    import shlex
    from subprocess import Popen, PIPE

    node_to_use = util.return_unused_node()
    if node_to_use:
        # TODO: rewrite this using the new command formatting?
        run_string = f"srun -w {node_to_use} --ntasks 1 --nodes 1 shifter --image={_DEFAULT_SHIFTER_IMAGE} " \
                     f"/bin/bash {_SHIFTER_BASH_FILE} python {_SHIFTER_SIREPO_SCRIPT}"
        run_string = ' '.join([run_string, name, input_file, *ignored_files])
        cmd = Popen(shlex.split(run_string), stderr=PIPE, stdout=PIPE)
        out, err = cmd.communicate()
        if err:
            print(err.decode())
            raise Exception('Model load from Sirepo in Shifter failed.')
        d = pickle.loads(out)
    else:
        d = None

    return util.broadcast(d)


def _get_application_path(application_name: str) -> str:
    full_path = shutil.which(application_name)
    assert full_path, f"Could not find a path for application: {full_path}"
    return full_path


class Setup(abc.ABC):
    _REGISTRY = {}
    _REQUIRED_KEYS = ('execution_type',)  # code specific keys that are required
    _OPTIONAL_KEYS = ()  # code specific keys that are not required
    # keys that can be used by any code
    _KNOWN_KEYS = tuple(pkyaml.load_file(SETUP_SCHEMA)) + _REQUIRED_KEYS + _OPTIONAL_KEYS
    SERIAL_RUN_COMMAND = None
    PARALLEL_RUN_COMMAND = None
    NAME = None
    SHIFTER_COMMAND = '--image={SHIFTER_IMAGE} --entrypoint'

    def __init__(self):
        self.setup = {
            'cores': 1
        }
        self.input_file_model = None
        self.validators = {'execution_type': _validate_execution_type}
        self.handlers = {'preprocess': self._handle_preprocess,
                         'postprocess': self._handle_postprocess}
        self.preprocess = []
        self.postprocess = []

    @classmethod
    def register_setup(cls):
        # class Inner:
        #     def __call__(self):
        #         cls._REGISTRY[setup_class.NAME] = setup_class
        #         return setup_class

        def inner(setup_class):
            cls._REGISTRY[setup_class.NAME] = setup_class
            return setup_class

        return inner

    @classmethod
    def get_setup(cls, setup: dict, code: str) -> 'Setup' or 'SetupTemplated':
        # verify execution type exists
        cls.check_setup(setup)

        # TODO: rsmpi or mpi should change the run command
        execution_type = setup['execution_type']

        # verify requirements for given execution_type are met in setup
        cls._REGISTRY[code].check_setup(setup)

        return cls._REGISTRY[code]

    @classmethod
    def check_setup(cls, setup: dict) -> None:
        # Check globally required keys exist
        for key in cls._REQUIRED_KEYS:
            assert setup.get(key), f"{key} must be defined in each setup block"

    @classmethod
    def templated(cls):
        return cls.NAME in TEMPLATED_CODES

    @classmethod
    def parse_input_file(cls, input_file: str, shifter: bool,
                         ignored_files: typing.Optional[typing.List[str]] = None) -> typing.Type['sirepo.lib.SimData'] \
                                                                                     or None:

        if shifter:
            # Must pass a list to ignored_files here since it is sent to subprocess
            d = _shifter_parse_model(cls.NAME, input_file, ignored_files or [])
        else:
            import sirepo.lib
            d = sirepo.lib.Importer(cls.NAME, ignored_files).parse_file(input_file)

        return d


    def format_task_string(self, is_parallel: bool) -> str:
        task_string = '{shifter_setup} {shifter_app} {app_arguments} {filename}'
        if self.setup.get('execution_type') == 'shifter':
            shifter_setup = self.SHIFTER_COMMAND.format(
                SHIFTER_IMAGE=self.setup.get('shifter_image', _DEFAULT_SHIFTER_IMAGE)
            )
            shifter_app = self._get_run_command(is_parallel)
        else:
            shifter_setup = ''
            shifter_app = ''

        app_arguments = " ".join([f"{k} {v if v else ''}" for k, v in self.setup.get('code_arguments', {}).items()])

        task_string = task_string.format(shifter_setup=shifter_setup,
                                         shifter_app=shifter_app,
                                         app_arguments=app_arguments,
                                         filename=pathlib.Path(
                                             self.setup.get('input_file', '')
                                         ).name
                                         )

        return task_string


    @property
    def get_ignored_files(self) -> list:
        ignored_file_list = self.setup.get('ignored_files')
        if ignored_file_list:
            assert type(ignored_file_list) == list, f"ignored files for code {self.NAME} as not a list"
            return ignored_file_list
        return []

    @property
    def input_file_path(self) -> pathlib.Path:
        p = pathlib.Path(self.setup.get('input_file') or '')

        return p.parent

    @abc.abstractmethod
    def generate_input_file(self, kwarg_dict: dict, directory: str, is_parallel: bool):
        pass

    def parse(self, name, value):
        self.validate_input(name, value)
        self.process_input(name, value)
        self.setup[name] = value

    def validate_input(self, key: str, value: str or float or int) -> None:
        if self.validators.get(key):
            if self.validators[key](value):
                return
            else:
                raise ValueError(f'{value} is not a recognized value for f{key}')

    def process_input(self, key: str, value: str or float or int) -> str or float or int:
        # Handling for special inputs
        if self.handlers.get(key):
            return self.handlers[key](value)
        else:
            return value

    def _get_run_command(self, is_parallel: bool) -> str:
        if is_parallel:
            run_command = self.PARALLEL_RUN_COMMAND
        else:
            run_command = self.SERIAL_RUN_COMMAND

        return run_command

    def get_run_command(self, is_parallel: bool) -> str:

        if self.setup.get('execution_type') == 'shifter':
            run_command = 'shifter'
            return _get_application_path(run_command)

        run_command = self._get_run_command(is_parallel)

        return _get_application_path(run_command)

    def get_sym_link_targets(self) -> set:
        return set()

    def _handle_preprocess(self, value: typing.List[str]) -> bool:
        # Run in the rsopt calling directory, not worker directories
        module_path, function_name = value
        module = pkrunpy.run_path_as_module(module_path)
        function = getattr(module, function_name)
        self.preprocess.append(function)
        return True

    def _handle_postprocess(self, value: typing.List[str]) -> bool:
        # Run in the rsopt calling directory, not worker directories
        module_path, function_name = value
        module = pkrunpy.run_path_as_module(module_path)
        function = getattr(module, function_name)
        self.postprocess.append(function)
        return True


class SetupTemplated(Setup):
    @abc.abstractmethod
    def _edit_input_file_schema(self, kwargs):
        pass
