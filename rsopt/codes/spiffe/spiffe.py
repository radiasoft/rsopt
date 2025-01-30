import typing
from rsopt.configuration.schemas import code

class Spiffe(code.Code):
    code: typing.Literal['spiffe']

    @classmethod
    def serial_run_command(cls) -> str or None:
        return 'spiffe'

    @classmethod
    def parallel_run_command(cls) -> str or None:
        return 'spiffe'
