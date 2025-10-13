import jinja2
import pathlib
import pydantic
import sys
import typing
from rsopt.configuration.schemas import code
from rsopt.configuration.schemas import setup as setup_schema
from rsopt import util

_PARALLEL_PYTHON_TEMPLATE = 'run_parallel_python.py.jinja'
_PARALLEL_PYTHON_RUN_FILE = 'run_parallel_python.py'
_TEMPLATE_PATH = util.package_data_path()


class Setup(setup_schema.Setup):
    input_file: pydantic.FilePath = None
    module: str = None
    serial_python_mode: typing.Literal["process", "thread", "worker"] = 'worker'
    function: str or callable
    argument_passing: code.ArgumentModes = pydantic.Field(code.ArgumentModes.KWARGS)


class Python(code.Code):
    code: typing.Literal["python"]
    setup: Setup

    _function: typing.Callable

    @pydantic.model_validator(mode='after')
    def mutually_exclusive(self, obj: typing.Any) -> typing.Any:
        # Check for any mutually exclusive options in the code block
        assert (self.setup.input_file is None) ^ (self.setup.module is None), \
            f"Configuration defines input_file={self.setup.input_file} and module={self.setup.module}. Only one may be given."

        return self


    @pydantic.model_validator(mode='after')
    def instantiate_function(self):
        # libEnsemble workers change active directory - sys.path will not record locally available modules
        if self.setup.input_file:
            sys.path.append('.')

            module = util.run_path_as_module(self.setup.input_file)
            function = getattr(module, self.setup.function)
            self._function = function
        elif self.setup.module:
            import importlib
            module = importlib.import_module(self.setup.module)
            function = getattr(module, self.setup.function)
            self._function = function
        else:
            # Pydantic validation should make sure this is never reached... in theory
            raise NotImplementedError("Either module or input_file must be defined in a Python setup block.")

        return self

    @property
    def get_function(self) -> typing.Callable:
        return self._function

    @classmethod
    def serial_run_command(cls) -> str or None:
        """Python's serial run command in s a special case. Unless the 'force_executor' flag is set, it should not be
        used since python code will either be run directly by the worker process in some manner or parallel
        execution is requested and the parallel run command branch is followed."""
        return 'python'

    @classmethod
    def parallel_run_command(cls) -> str or None:
        return 'python'

    @property
    def _get_filename(self) -> str:
        # Serial python is run on worker so this is never used unless is_parallel==True
        filename = _PARALLEL_PYTHON_RUN_FILE

        return filename

    @property
    def run_file_name(self) -> str:
        """File name used to construct task string for the Executor."""
        # Usually there is no reason not to use the input file name
        # Parallel Python jobs require a different name because a run file is constructed that imports the run function
        #  from the input file

        # Serial python is run on worker so this is never used unless is_parallel==True
        return _PARALLEL_PYTHON_RUN_FILE

    @property
    def get_sym_link_targets(self) -> set:
        if self.use_executor and self.setup.input_file is not None:
            return {self.setup.input_file}
        return set()

    @property
    def use_executor(self) -> bool:
        if self.setup.force_executor or self.use_mpi:
            return True
        return False

    def generate_input_file(self, kwarg_dict, directory, is_parallel):
        if not self.use_executor:
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
                                          full_input_file_path=self.setup.input_file,
                                          input_module_name=self.setup.module,
                                          function=self.setup.function)

        file_path = pathlib.Path(directory).joinpath(_PARALLEL_PYTHON_RUN_FILE)

        with open(file_path, 'w') as ff:
            ff.write(output_template)

