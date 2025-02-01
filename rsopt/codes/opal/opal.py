import typing
from rsopt.codes.elegant import elegant
from rsopt.configuration.schemas import setup as setup_schema

class Setup(setup_schema.Setup):
    pass

class Opal(elegant.Elegant):
    code: typing.Literal['opal'] = 'opal'
    setup: Setup

    @classmethod
    def serial_run_command(cls) -> str or None:
        return 'opal'

    @classmethod
    def parallel_run_command(cls) -> str or None:
        return 'opal'
