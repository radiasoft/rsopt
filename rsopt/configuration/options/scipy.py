from rsopt.configuration.options import Options


class Scipy(Options):
    NAME = 'scipy'
    # Ordering of required keys matters to validate method assignment is correct
    REQUIRED_OPTIONS = ('method', 'exit_criteria')
    # Only can allow what aposmm_localopt_support handles right now
    # SciPy routines are internally named ['scipy_Nelder-Mead', 'scipy_COBYLA', 'scipy_BFGS']
    # Will use same aliases as scipy uses in keeping with nlopt, and prefix here
    ALLOWED_METHODS = ('Nelder-Mead', 'COBYLA', 'BFGS')

    _opt_return_codes = {'Nelder-Mead': [0],
                         'COBYLA': [1],
                         'BFGS': [0]}

    @classmethod
    def _check_options(cls, options):
        for key in cls.REQUIRED_OPTIONS:
            assert options.get(key), f"{key} must be defined in options to use {cls.NAME}"
        proposed_method = options.get(cls.REQUIRED_OPTIONS[0])
        assert proposed_method in cls.ALLOWED_METHODS, \
            f"{proposed_method} not available for use in software {cls.NAME}"

        if 'software_options' in options.keys():
            options['software_options'].setdefault('opt_return_codes', cls._opt_return_codes[options.get('method')])
        else:
            options['software_options'] = {'opt_return_codes': cls._opt_return_codes[options.get('method')]}