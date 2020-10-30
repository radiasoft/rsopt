from pykern import pkrunpy

class Options:
    __REQUIRED_KEYS = ('software',)
    REQUIRED_KEYS = ()

    def __init__(self):
        self.objective_function = []
        self.exit_criteria = {}
        self.software_options = {}
        self.executor_options = {}
        self.method = ''

    @classmethod
    def get_option(cls, options):
        # Required setup checks for options
        cls.__check_options(options)
        software = options.pop('software')

        # Implementation specific checks
        option_classes[software]._check_options(options)

        return option_classes[software]

    @classmethod
    def __check_options(cls, options):
        for key in cls.__REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options"

    @classmethod
    def _check_options(cls, options):
        name = cls.NAME
        for key in cls.REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options for {name}"

    def _validate_input(self, name, value):
        # If the name isn't registered then no point checking further
        name_pass = hasattr(self, name)
        if not name_pass:
            print(f'{name} in options not recognized. It will be ignored.')
            return False
        # Check all other values defined in init
        else:
            expected_type = type(getattr(self, name))
            value_pass = isinstance(value, expected_type)
            if not value_pass:
                received_type = type(value)
                print(f'{name} must be type {expected_type}, but received {received_type}')
                return False

        return True

    def parse(self, name, value):
        # Options has a fairly strict set of expected values
        # so we can impose more checks here compared to other categories
        if self._validate_input(name, value):
            self.__setattr__(name, value)

    def get_objective_function(self):
        if len(self.objective_function) == 2:
            module_path, function = self.objective_function
            module = pkrunpy.run_path_as_module(module_path)
            function = getattr(module, function)
        else:
            function = None

        return function

class Nlopt(Options):
    NAME = 'nlopt'
    # Ordering of required keys matters to validate method assignment is correct
    REQUIRED_KEYS = ('method', 'exit_criteria')
    # Only can allow what aposmm_localopt_support handles right now
    ALLOWED_METHODS = ('LN_BOBYQA', 'LN_SBPLX', 'LN_COBYLA', 'LN_NEWUOA',
                         'LN_NELDERMEAD', 'LD_MMA')

    @classmethod
    def _check_options(cls, options):
        for key in cls.REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options to use {cls.NAME}"
        proposed_method = options.get(cls.REQUIRED_KEYS[0])
        assert proposed_method in cls.ALLOWED_METHODS, \
            f"{proposed_method} not available for use in software {cls.NAME}"


class Aposmm(Options):
    NAME = 'aposmm'
    REQUIRED_KEYS = ('method', 'exit_criteria')
    # Only can allow what aposmm_localopt_support handles right now
    ALLOWED_METHODS = ('LN_BOBYQA', 'LN_SBPLX', 'LN_COBYLA', 'LN_NEWUOA',
                         'LN_NELDERMEAD', 'LD_MMA')
    SOFTWARE_OPTIONS = {
        'high_priority_to_best_localopt_runs': True,
        'max_active_runs': 1,
        'initial_sample_size': 0
    }

    def __init__(self):
        super().__init__()

        self.nworkers = 2
        for key, val in self.SOFTWARE_OPTIONS.items():
            self.__setattr__(key, val)

    # def get_software_options(self):
    #     options_dict = {}
    #     for key in self.SOFTWARE_OPTIONS.keys():
    #         options_dict[key] = self.__getattribute__(key)
    #
    #     return options_dict

class Nsga2(Options):
    NAME = 'nsga2'
    REQUIRED_KEYS = ('software_options', 'exit_criteria', )
    SOFTWARE_OPTIONS = {
        'n_objectives': None  # Must be set by user
    }
    def __init__(self):
        super().__init__()
        for key, val in self.SOFTWARE_OPTIONS.items():
            self.__setattr__(key, val)

    @classmethod
    def _check_options(cls, options):
        for key in cls.REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options to use {cls.NAME}"
        assert options['software_options'].get('n_objectives'), "The number of objectives for NSGA-II must be " \
                                                                "specified in options: software_options: n_objectives"
        try:
            int(options['software_options'].get('n_objectives'))
        except ValueError:
            nobj = repr(options['software_options'].get('n_objectives'))
            raise ValueError('{} is not a valid number of objectives for `n_objectives'.format(nobj))



class Mesh(Options):
    NAME = 'mesh_scan'
    REQUIRED_KEYS = ()

    def __init__(self):
        super().__init__()
        self.nworkers = 1
        self.mesh_file = ''

option_classes = {
    'nlopt': Nlopt,
    'aposmm': Aposmm,
    'mesh_scan': Mesh
}

