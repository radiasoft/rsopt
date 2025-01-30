import jinja2
import pydantic
import sys
import typing
from rsopt.configuration.schemas import code
from rsopt.configuration.schemas import setup as setup_schema
from rsopt import util

_PARALLEL_PYTHON_TEMPLATE = 'run_parallel_python.py.jinja'
_PARALLEL_PYTHON_RUN_FILE = 'run_parallel_python.py'
_TEMPLATE_PATH = pkio.py_path(pkresource.filename(''))

class Setup(setup_schema.Setup):
    input_File: pydantic.FilePath
    serial_python_mode: typing.Literal["process", "thread", "worker"] = 'worker'
    function: str or callable

class Python(code.Code):
    code: typing.Literal["python"]
    setup: Setup

    _function: callable

    @pydantic.field_validator('setup', mode='after')
    def instantiate_function(self):
        # libEnsemble workers change active directory - sys.path will not record locally available modules
        sys.path.append('.')

        module = util.run_path_as_module(self.setup.input_file)
        function = getattr(module, self.setup['function'])
        self._function = function

    @classmethod
    def serial_run_command(cls) -> str or None:
        # serial not executed by Executor subprocess so no run command is needed
        return None

    @classmethod
    def parallel_run_command(cls) -> str or None:
        return 'python'

    @property
    def _get_filename(self) -> str:
        # Serial python is run on worker so this is never used unless is_parallel==True
        filename = _PARALLEL_PYTHON_RUN_FILE

        return filename

    def get_sym_link_targets(self) -> set:
        return {self.setup.input_file}

    def generate_input_file(self, kwarg_dict, directory, is_parallel):
        if not is_parallel and not self.setup.get('force_executor', False):
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

