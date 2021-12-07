from rsopt.configuration.options import Options


class pySOT(Options):
    NAME = 'pysot'
    REQUIRED_OPTIONS = ('exit_criteria',)
    SOFTWARE_OPTIONS = {}

    def __init__(self):
        super().__init__()
        self.nworkers = 2
        self.method = 'pysot'