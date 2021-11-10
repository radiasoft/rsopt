from pykern import pkrunpy
import sys
import os


class Options:
    __REQUIRED_KEYS = ('software',)
    REQUIRED_KEYS = ()

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


class Scipy(Options):
    NAME = 'scipy'
    # Ordering of required keys matters to validate method assignment is correct
    REQUIRED_KEYS = ('method', 'exit_criteria')
    # Only can allow what aposmm_localopt_support handles right now
    # SciPy routines are internally named ['scipy_Nelder-Mead', 'scipy_COBYLA', 'scipy_BFGS']
    # Will use same aliases as scipy uses in keeping with nlopt, and prefix here
    ALLOWED_METHODS = ('Nelder-Mead', 'COBYLA', 'BFGS')

    _opt_return_codes = {'Nelder-Mead': [0],
                         'COBYLA': [1],
                         'BFGS': [0]}

    @classmethod
    def _check_options(cls, options):
        for key in cls.REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options to use {cls.NAME}"
        proposed_method = options.get(cls.REQUIRED_KEYS[0])
        assert proposed_method in cls.ALLOWED_METHODS, \
            f"{proposed_method} not available for use in software {cls.NAME}"

        if 'software_options' in options.keys():
            options['software_options'].setdefault('opt_return_codes', cls._opt_return_codes[options.get('method')])
        else:
            options['software_options'] = {'opt_return_codes': cls._opt_return_codes[options.get('method')]}


class Dfols(Options):
    NAME = 'dfols'
    REQUIRED_KEYS = ('exit_criteria', 'components')

    def __init__(self):
        super().__init__()
        self.components = 1

    @classmethod
    def _check_options(cls, options):
        for key in cls.REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options to use {cls.NAME}"

        if 'software_options' in options.keys():
            options['software_options'].setdefault('components', options.get('components'))
        else:
            options['software_options'] = {'components': options.get('components')}

    def get_sim_specs(self):
        sim_specs = {
            'in': ['x'],
            'out': [('f', float), ('fvec', float, self.components)]
        }

        return sim_specs


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

        self.load_start_sample = ''

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
    REQUIRED_KEYS = ('n_objectives', 'exit_criteria', )
    SOFTWARE_OPTIONS = {}

    def __init__(self):
        super().__init__()
        self.n_objectives = 0
        self.nworkers = 2
        self.pop_size = 100
        # for key, val in self.SOFTWARE_OPTIONS.items():
        #     self.__setattr__(key, val)

    def get_sim_specs(self):
        sim_specs = {
            'in': ['individual'],
            'out': [('fitness_values', float, self.n_objectives)]
        }

        return sim_specs


    # @classmethod
    # def _check_options(cls, options):
    #     for key in cls.REQUIRED_KEYS:
    #         assert options.get(key), f"{key} must be defined in options to use {cls.NAME}"
    #     try:
    #         int(options['software_options'].get('n_objectives'))
    #         if options['software_options'].get('n_objectives') == 0:
    #             raise ValueError('The option `n_objectives` must be set to a non-zero value for NSGA2')
    #     except ValueError:
    #         nobj = repr(options['software_options'].get('n_objectives'))
    #         raise ValueError('{} is not a valid number of objectives for `n_objectives'.format(nobj))


class pySOT(Options):
    NAME = 'pysot'
    REQUIRED_KEYS = ('exit_criteria',)
    SOFTWARE_OPTIONS = {}

    def __init__(self):
        super().__init__()
        self.nworkers = 2
        self.method = 'pysot'


class Dlib(Options):
    NAME = 'dlib'
    REQUIRED_KEYS = ('exit_criteria',)
    SOFTWARE_OPTIONS = {}

    def __init__(self):
        super().__init__()
        self.nworkers = 2
        self.method = 'dlib'


class Mesh(Options):
    NAME = 'mesh_scan'
    REQUIRED_KEYS = ()

    def __init__(self):
        super().__init__()
        self.nworkers = 1
        self.mesh_file = ''


class LH(Options):
    NAME = 'lh_scan'
    REQUIRED_KEYS = ('batch_size',)

    def __init__(self):
        super().__init__()
        self.nworkers = 1
        self.seed = None
        self.batch_size = 0


option_classes = {
    'nlopt': Nlopt,
    'aposmm': Aposmm,
    'nsga2': Nsga2,
    'dfols': Dfols,
    'scipy': Scipy,
    'pysot': pySOT,
    'dlib': Dlib,
    'mesh_scan': Mesh,
    'lh_scan': LH
}

