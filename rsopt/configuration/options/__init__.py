from enum import Enum
from rsopt.configuration.options import dfols, dlib, pysot, lh, nsga2, scipy
from rsopt.configuration.options import mesh


class SUPPORTED_OPTIONS(Enum):
    mesh_scan = ('sample', mesh.Mesh)
    dfols = ('optimize', dfols.Dfols)
    dlib = ('optimize', dlib.Dlib)
    pysot = ('optimize', pysot.Pysot)
    lh_scan = ('sample', lh.LH)
    nsga2 = ('optimize', nsga2.Nsga2)
    scipy = ('optimize', scipy.Scipy)

    def __init__(self, typing, model):
        self.typing = typing
        self.model = model

    @classmethod
    def get_sample_names(cls) -> tuple[str, ...]:
        """Returns a list of option names that can be used by sample command"""
        return tuple([name for name, member in cls.__members__.items() if member.value[0] == 'sample'])

    @classmethod
    def get_sample_models(cls) -> tuple:
        """Returns a list of models for options that can be used by sample command"""
        return tuple([name.model for name in cls if getattr(cls, name.name).value[0] == 'sample'])

    @classmethod
    def get_optimize_names(cls) -> tuple[str, ...]:
        """Returns a list of option names that can be used by optimize command"""
        return tuple([name for name, member in cls.__members__.items() if member.value[0] == 'optimize'])

    @classmethod
    def get_optimize_models(cls) -> tuple:
        """Returns a list of models for options that can be used by optimize command"""
        return tuple([name.model for name in cls if getattr(cls, name.name).value[0] == 'optimize'])
