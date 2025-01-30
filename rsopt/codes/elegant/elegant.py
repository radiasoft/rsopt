import typing
from rsopt.configuration.schemas import code
from rsopt.configuration.schemas import setup as setup_schema

class Setup(setup_schema.Setup):
    madeup_requirement: str

class Elegant(code.Code):
    code: typing.Literal['elegant']
    setup: Setup

    @classmethod
    def serial_run_command(cls) -> str or None:
        return 'elegant'

    @classmethod
    def parallel_run_command(cls) -> str or None:
        return 'Pelegant'
