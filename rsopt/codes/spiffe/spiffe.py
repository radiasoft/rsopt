import typing
from rsopt.configuration.schemas import code

class Spiffe(code.Code):
    code: typing.Literal['spiffe']
