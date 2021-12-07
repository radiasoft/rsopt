from pykern import pkrunpy
from pykern import pkyaml
from rsopt import _OPTIONS_SCHEMA, _OPTIMIZER_SCHEMA
import sys
import os


_TYPE_MAPPING = {
    # Map typing from schema to Python types
    'None': type(None),
    'bool': bool,
    'str': str,
    'int': int,
    'float': float,
    'list': list,
    'dict': dict
}


class Options:
    NAME = 'options'
    __REQUIRED_KEYS = ('software',)
    _REGISTERED_OPTIONS = pkyaml.load_file(_OPTIONS_SCHEMA)
    _OPT_SCHEMA = pkyaml.load_file(_OPTIMIZER_SCHEMA)
    REQUIRED_OPTIONS = ()

    def __init__(self):
        self.objective_function = []
        self.exit_criteria = {}
        self.software_options = {}
        self.executor_options = {}
        self.software = ''
        self.method = ''
        self.sym_links = []
        self.nworkers = 2
        self.use_worker_dirs = False
        self.sim_dirs_make = False
        self.run_dir = './ensemble'
        self.record_interval = 0
        self.output_file = ''

    @classmethod
    def get_option(cls, options_instance):
        # Imported locally to prevent circular dependency
        from rsopt.configuration.options.options import option_classes

        # Required setup checks for options
        cls.__check_options(options_instance)
        software = options_instance.pop('software')

        # Implementation specific checks
        option_classes[software]._check_options(options_instance)

        return option_classes[software]

    @classmethod
    def __check_options(cls, options):
        # First check for options required by base class
        # Inherited classes check for their requirements with _check_options
        for key in cls.__REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options"

    @classmethod
    def _check_options(cls, options):
        name = cls.NAME
        for key in cls.REQUIRED_OPTIONS:
            assert options.get(key), f"{key} must be defined in options for {name}"

    def _validate_input(self, name, value):
        co = self._REGISTERED_OPTIONS[self.NAME]
        if name not in co.keys() and name not in self.REQUIRED_OPTIONS:
            raise KeyError(f'options {name} was not recognized')
        else:
            allowed_types = co[name]['typing']
            value_pass = isinstance(value, tuple(_TYPE_MAPPING[t] for t in allowed_types))
            if not value_pass:
                received_type = type(value)
                raise TypeError(f'{name} must be one of types {allowed_types}, but received {received_type}')

        return True

    def parse(self, name, value):
        # Options has a fairly strict set of expected values
        # so we can impose more checks here compared to other categories
        if self._validate_input(name, value):
            self.__setattr__(name, value)

    def get_objective_function(self):
        if len(self.objective_function) == 2:
            module_path, function = self.objective_function
            sys.path.append(os.getcwd())
            module = pkrunpy.run_path_as_module(module_path)
            function = getattr(module, function)
        else:
            function = None

        return function

    def get_sim_specs(self):
        sim_specs = {
            'in': ['x'],
            'out': [('f', float), ]
        }

        return sim_specs


