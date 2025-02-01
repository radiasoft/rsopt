import copy
import os
import pydantic
import typing
from functools import cached_property
from rsopt.codes.flash.parse import parse_file
from rsopt.configuration.schemas import code
from rsopt.configuration.schemas import setup as setup_schema


def _write_file(par_dict: dict, new_par_path: str) -> None:
    """Write a dictionary of parameters/values to a `flash.par` file."""

    text = []

    for key, val in par_dict.items():
        text.append("{} = {} \n".format(key.strip(), val))

    with open(new_par_path, 'w') as ff:
        ff.write(''.join(text))

class _Model:
    """Simple class to emulate what we need from a sirepo model"""
    def __init__(self, kwarg_dict):
        self.kwarg_dict = kwarg_dict

    def write_files(self, directory: str) -> None:
        return _write_file(self.kwarg_dict, directory)

class Setup(setup_schema.Setup):
    executable: pydantic.FilePath

    @pydantic.field_validator('executable', mode='after')
    @classmethod
    def check_executable(cls, v: str):
        assert os.access(v, os.X_OK), f"FLASH executable {v} does not have execution permission"
        return v


class Flash(code.Code):
    code: typing.Literal['flash'] = 'flash'
    setup: Setup

    def serial_run_command(self) -> str or None:
        return './' + str(self.setup.executable)

    def parallel_run_command(self) -> str or None:
        return './' + str(self.setup.executable)

    def generate_input_file(self, kwarg_dict: dict, directory: str, is_parallel: bool) -> None:
        # `directory` is not used for the flash file write because it does not go through sirepo.lib
        model = self._edit_input_file_schema(kwarg_dict)

        # This function is always being called in a worker run directory so path is just file name
        model.write_files(self.setup.input_file.name)

    def _edit_input_file_schema(self, kwarg_dict: dict) -> _Model:
        # This editor has no protection on value typing because we have no Sirepo schema
        model = copy.deepcopy(self.input_file_model)
        for n, v in kwarg_dict.items():
            # Parser sets all keys to be lower case
            n_lower = n.lower()
            assert n_lower in model.keys(), f"Parameter/Setting: {n} is not defined and cannot be edited."
            model[n_lower] = v

        model = _Model(model)

        return model

    @cached_property
    def input_file_model(self) -> dict or None:
        d = parse_file(self.setup.input_file)

        return d