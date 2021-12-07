from rsopt.configuration.options import Options


class Mesh(Options):
    NAME = 'mesh_scan'
    REQUIRED_OPTIONS = ()

    def __init__(self):
        super().__init__()
        self.nworkers = 1
        self.mesh_file = ''