from rsopt.configuration.options import Options


class Nlopt(Options):
    NAME = 'nlopt'
    # Ordering of required keys matters to validate method assignment is correct
    REQUIRED_OPTIONS = ('method', 'exit_criteria')
    # Only can allow what aposmm_localopt_support handles right now
    ALLOWED_METHODS = ('LN_BOBYQA', 'LN_SBPLX', 'LN_COBYLA', 'LN_NEWUOA',
                         'LN_NELDERMEAD', 'LD_MMA')

    @classmethod
    def _check_options(cls, options):
        for key in cls.REQUIRED_OPTIONS:
            assert options.get(key), f"{key} must be defined in options to use {cls.NAME}"
        proposed_method = options.get(cls.REQUIRED_OPTIONS[0])
        assert proposed_method in cls.ALLOWED_METHODS, \
            f"{proposed_method} not available for use in software {cls.NAME}"