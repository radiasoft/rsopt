import os
from pykern import pkio, pkrunpy
from rsopt.configuration.setup.setup import Setup
from rsopt.configuration.setup.python import Python
from rsopt.configuration.setup.setup import Setup

@Setup.register_setup()
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

    @classmethod
    def _check_setup(cls, setup):
        # Check globally required keys exist
        code = cls.NAME
        for key in cls.__REQUIRED_KEYS:
            assert setup.get(key), f"{key} must be defined in setup for {code}"
        # Validate for all keys (field in config file) are known to setup
        for key in setup.keys():
            # Can be made private if non-required code-specific fields are ever added
            if key not in (cls._KNOWN_KEYS + cls.__REQUIRED_KEYS):
                raise KeyError(f'{key} in setup block for code-type {code} is not recognized.')
        Setup._check_setup(setup)

    def get_sym_link_targets(self):
        if self.setup['input_file'] not in self.setup['file_mapping'].values():
            # If file name in file_mapping then input_file being created dynamically, otherwise copy here
            return {self.setup['input_file']}

        return set()

    def generate_input_file(self, kwarg_dict, directory):

        # Get strings for each file and fill in arguments for this job
        for key, val in self.setup['file_mapping'].items():
            local_file_instance = self.get_file_def_module().__getattribute__(key).format(**kwarg_dict)
            pkio.write_text(os.path.join(directory, val), local_file_instance)
