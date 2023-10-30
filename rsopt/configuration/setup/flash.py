import copy
import re
import typing
from rsopt.configuration.setup.setup import SetupTemplated

def _parse_file(par_path: str) -> dict:
    """Read in a FLASH .par file and return a dictionary of parameters and values."""

    res = {}
    par_text = open(par_path)

    for line in par_text.readlines():
        line = re.sub(r"#.*$", "", line)
        m = re.search(r"^(\w.*?)\s*=\s*(.*?)\s*$", line)
        if m:
            f, v = m.group(1, 2)
            res[f.lower()] = v
    return res


def _write_file(par_dict: dict, new_par_path: str) -> None:
    """Write a dictionary of parameters/values to a `flash.par` file."""

    text = []

    for key, val in par_dict.items():
        text.append("{} = {} \n".format(key.strip(), val))

    with open(new_par_path, 'w') as ff:
        ff.write(''.join(text))

class _Model:
    def __init__(self, kwarg_dict):
        self.kwarg_dict = kwarg_dict

    def write_files(self, directory: str) -> None:
        return _write_file(self.kwarg_dict, directory)

def _is_executable(executable_name):
    import os
    assert os.path.isfile(executable_name), f"Could not find the FLASH executable: {executable_name}"
    assert os.access(executable_name, os.X_OK), f"FLASH executable {executable_name} does not have execution permission"

    return True

@SetupTemplated.register_setup()
class Flash(SetupTemplated):
    __REQUIRED_KEYS = ('input_file', 'executable')
    # Run commands for flash are set at runtime by _get_run_command
    SERIAL_RUN_COMMAND = './'
    PARALLEL_RUN_COMMAND = './'
    NAME = 'flash'

    def __init__(self):
        super().__init__()
        self.validators['executable'] = _is_executable

    def _get_run_command(self, is_parallel: bool) -> str:
        # setup['executable'] guaranteed to exist at run time by self.check_setup
        if is_parallel:
            run_command = self.PARALLEL_RUN_COMMAND + self.setup['executable']
        else:
            run_command = self.SERIAL_RUN_COMMAND + self.setup['executable']

        return run_command

    # TODO: I don't like that this now has to return a dict - breaks with super
    @classmethod
    def parse_input_file(cls, input_file: str, shifter: bool,
                         ignored_files: typing.Optional[typing.List[str]] = None) -> dict:

        d = _parse_file(input_file)

        return d

    def _edit_input_file_schema(self, kwarg_dict:dict) -> _Model:
        # TODO: This has no protection on value typing because we have no Sirepo schema

        model = copy.deepcopy(self.input_file_model)
        for n, v in kwarg_dict.items():
            model[n] = v

        model = _Model(model)

        return model

    def generate_input_file(self, kwarg_dict, directory, is_parallel):
        # `directory` is not used for the flash file write because it does not go through sirepo.lib
        model = self._edit_input_file_schema(kwarg_dict)

        # This function is always being called in a worker run directory so path is just file name
        model.write_files(self.setup['input_file'])
