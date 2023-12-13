from rsopt.configuration.options import Options


class LH(Options):
    NAME = 'lh_scan'
    REQUIRED_OPTIONS = ('batch_size',)

    def __init__(self):
        super().__init__()
        self.use_zero_resource = False
        self.nworkers = 1
        self.batch_size = 0