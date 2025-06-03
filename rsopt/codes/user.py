import typing
import pathlib
import pydantic
from rsopt.configuration.schemas import code
from rsopt.configuration.schemas import setup as setup_schema
from rsopt import util
class Setup(setup_schema.Setup):
    run_command: str
    file_mapping: dict = pydantic.Field(default_factory=dict)
    input_file: str = ''
    file_definitions: pydantic.FilePath = None

    @pydantic.field_validator("input_file", mode="before")
    @classmethod
    def coerce_none_to_empty(cls, v):
        # Setup for user mode should accept an explicit value of None
        return "" if v is None else v

class User(code.Code):
    code: typing.Literal['user'] = 'user'
    setup: Setup

    @property
    def serial_run_command(self) -> str or None:
        return self.setup.run_command

    @property
    def parallel_run_command(self) -> str or None:
        return self.setup.run_command

    def generate_input_file(self, kwarg_dict: dict, directory: str, is_parallel: bool) -> None:
        # Get strings for each file and fill in arguments for this job
        base_run_path = pathlib.Path.cwd().expanduser()

        for key, val in self.setup.file_mapping.items():
            module_path = pathlib.Path(base_run_path).joinpath(self.setup.file_definitions)
            module = util.run_path_as_module(module_path)

            local_file_instance = module().__getattribute__(key).format(**kwarg_dict)
            with open(pathlib.Path(directory).joinpath(val), 'w') as ff:
                ff.write(local_file_instance)
