import typing
from rsopt.codes import elegant
from rsopt.configuration.schemas import setup as setup_schema

class Setup(setup_schema.Setup):
    pass

class Genesis(elegant.Elegant):
    code: typing.Literal['genesis'] = 'genesis'
    setup: Setup

    @classmethod
    def serial_run_command(cls) -> str or None:
        return 'genesis'

    @classmethod
    def parallel_run_command(cls) -> str or None:
        return 'genesis_mpi'
