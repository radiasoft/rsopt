from rsopt.configuration.options import Options


class Nsga2(Options):
    NAME = 'nsga2'
    REQUIRED_OPTIONS = ('n_objectives', 'exit_criteria',)
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