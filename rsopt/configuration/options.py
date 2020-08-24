

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
            assert options.get(key), f"{key} mustself.__NAME be defined in options"

    @classmethod
    def _validate_input(cls, name, value):
        # If the name isn't registered then no point checking further
        name_pass = hasattr(cls, name)
        if not name_pass:
            print(f'{name} in options not recognized. It will be ignored.')
            return False

        # Check special cases for values
        if name == 'objective_function':
            if value:
                assert callable(value), "f{name} must be either None or callable"
        # Check all other values defined in init
        else:
            expected_type = type(getattr(cls, name))
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
    __REQUIRED_KEYS = ('method', 'exit_criteria')
    # Only can allow what aposmm_localopt_support handles right now
    __ALLOWED_METHODS = ('LN_BOBYQA', 'LN_SBPLX', 'LN_COBYLA', 'LN_NEWUOA',
                         'LN_NELDERMEAD', 'LD_MMA')

    @classmethod
    def _check_options(cls, options):
        for key in cls.__REQUIRED_KEYS:
            assert options.get(key), f"{key} must be defined in options for f{cls.__NAME}"

option_classes = {
    'nlopt': Nlopt
}

