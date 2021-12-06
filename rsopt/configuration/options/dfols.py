import rsopt.configuration


class Dfols(rsopt.configuration.Options):
    NAME = 'dfols'
    REQUIRED_OPTIONS = ('exit_criteria', 'components')

    def __init__(self):
        super().__init__()
        self.components = 1
        self.method = 'dfols'

    @classmethod
    def _check_options(cls, options):
        for key in cls.REQUIRED_OPTIONS:
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