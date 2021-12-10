import rsopt.configuration


class Mobo(rsopt.configuration.Options):
    NAME = 'mobo'
    REQUIRED_OPTIONS = ('exit_criteria', 'objectives', 'constraints')

    def __init__(self):
        super().__init__()
        self.nworkers = 2
        self.objectives = 1
        self.constraints = 0
        self.method = 'mobo'
        self.reference = []

    def get_sim_specs(self):
        sim_specs = {
            'in': ['x'],
            'out': [('f', float, self.objectives), ('c', float, self.constraints)]
        }

        return sim_specs