from rsopt.configuration.options import Options
from rsopt.configuration import options


class Aposmm(Options):
    NAME = 'aposmm'
    REQUIRED_OPTIONS = ('method', 'exit_criteria', 'initial_sample_size')
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

    def get_sim_specs(self):
        # Imported locally to prevent circular dependency
        from rsopt.configuration.options.options import option_classes

        def split_method(method_name):
            software, method = method_name.split('.')
            return software, method
        software, method = split_method(self.method)
        sim_specs = self._OPT_SCHEMA[software]['methods'][method]['sim_specs']
        opt_method = option_classes[software]()
        for key in opt_method.REQUIRED_OPTIONS:
            if key == 'exit_criteria' or key == 'method':
                continue
            assert self.software_options.get(key), f'Use of {software}.{method} with APOSMM requires that {key} be ' \
                                                   f'set in software_options '
            opt_method.parse(key, self.software_options.pop(key))
        sim_specs['out'] = [tuple(t) if len(t) == 2 else (*t[:2], opt_method.__getattribute__(t[2])) for t in sim_specs['out']]
        return sim_specs