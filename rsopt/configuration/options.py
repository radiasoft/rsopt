

class Options:
    __REQUIRED_KEYS = ('software',)

    def __init__(self):
        self.objective_function = None
        self.exit_criteria = {}
        self.software_options = {}
        self.method = None

    @classmethod
    def get_option(cls, options):
        cls._check_options(options)
        software = options.pop('software')

        option_classes[software]._check_options(options)

        return option_classes[software]

    @classmethod
    def _check_options(cls, options):
        for key in cls.__REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options"

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


class Nlopt(Options):
    __NAME = 'nlopt'
    # Ordering of required keys matters to validate method assignment is correct
    __REQUIRED_KEYS = ('method', 'exit_criteria')
    # Only can allow what aposmm_localopt_support handles right now
    __ALLOWED_METHODS = ('LN_BOBYQA', 'LN_SBPLX', 'LN_COBYLA', 'LN_NEWUOA',
                         'LN_NELDERMEAD', 'LD_MMA')

    @classmethod
    def _check_options(cls, options):
        for key in cls.__REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options to use {cls.__NAME}"
        proposed_method = options.get(cls.__REQUIRED_KEYS[0])
        assert proposed_method in cls.__ALLOWED_METHODS, \
            f"{proposed_method} not available for use in software {cls.__NAME}"

option_classes = {
    'nlopt': Nlopt
}

