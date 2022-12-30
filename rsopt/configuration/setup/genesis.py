import os
import typing
from copy import deepcopy
from rsopt.configuration.setup.setup import SetupTemplated
from rsopt.configuration.setup.elegant import Elegant


def _create_sym_links(*args, link_location='default'):
    for filepath in args:
        if link_location == 'default':
            filename = os.path.split(filepath)[-1]
        else:
            filename = link_location
        os.symlink(filepath, filename)

@SetupTemplated.register_setup()
class Genesis(Elegant):
    __REQUIRED_KEYS = ('input_file',)
    NAME = 'genesis'
    SERIAL_RUN_COMMAND = 'genesis'
    PARALLEL_RUN_COMMAND = 'genesis_mpi'

    @classmethod
    def parse_input_file(cls, input_file: str, shifter: str,
                         ignored_files: typing.Optional[typing.List[str]] = None):
        # assumes lume-genesis can be installed locally - shifter execution not needed
        # expand_paths is not used to ensure that generated input files are used if desired -
        # otherwise rsopt symlinks them to run dir
        import genesis
        d = genesis.Genesis(input_file, use_tempdir=False, expand_paths=False, check_executable=False)

        return d

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

    def generate_input_file(self, kwarg_dict, directory, is_parallel):
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
