import jinja2
import os
import sys
import typing
from pykern import pkrunpy
from pykern import pkio
from pykern import pkresource
from rsopt.configuration.setup.setup import Setup, _get_application_path

_PARALLEL_PYTHON_TEMPLATE = 'run_parallel_python.py.jinja'
_PARALLEL_PYTHON_RUN_FILE = 'run_parallel_python.py'
_TEMPLATE_PATH = pkio.py_path(pkresource.filename(''))

@Setup.register_setup()
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
    def parse_input_file(cls, input_file: str, shifter: str,
                         ignored_files: typing.Optional[typing.List[str]] = None) -> None:
        # Python does not use text input files. Functions are dynamically imported by `function`.
        assert os.path.isfile(input_file), f'Could not find input_file: {input_file}'
        return None

    @classmethod
    def check_setup(cls, setup):
        # Check globally required keys exist
        code = cls.NAME
        for key in cls.__REQUIRED_KEYS:
            assert setup.get(key), f"{key} must be defined in setup for {code}"
        # Validate for all keys (field in config file) are known to setup
        for key in setup.keys():
            # Can be made private if non-required code-specific fields are ever added
            if key not in (cls._KNOWN_KEYS + cls.__REQUIRED_KEYS):
                raise KeyError(f'{key} in setup block for code-type {code} is not recognized.')
        Setup.check_setup(setup)

    def get_sym_link_targets(self):
        return {self.setup['input_file']}

    def generate_input_file(self, kwarg_dict, directory, is_parallel):
        if not is_parallel:
            return None

        template_loader = jinja2.FileSystemLoader(searchpath=_TEMPLATE_PATH)
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template(_PARALLEL_PYTHON_TEMPLATE)

        dict_item_str = {}
        for k, v in kwarg_dict.items():
            if type(v) == str:
                dict_item_str[k] = v
        for k in dict_item_str.keys():
            kwarg_dict.pop(k)

        output_template = template.render(dict_item=kwarg_dict, dict_item_str=dict_item_str,
                                          full_input_file_path=self.setup['input_file'],
                                          function=self.setup['function'])

        file_path = os.path.join(directory, _PARALLEL_PYTHON_RUN_FILE)

        with open(file_path, 'w') as ff:
            ff.write(output_template)

    def get_run_command(self, is_parallel: bool) -> str:

        if self.setup.get('execution_type') == 'shifter':
            run_command = 'shifter'
            return _get_application_path(run_command)
        if is_parallel:
            run_command = self._get_run_command(is_parallel)
            return _get_application_path(run_command)

        return ''