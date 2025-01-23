from rsopt.configuration.schemas.options import OptionsExit
import pydantic
import typing

class Dfols(OptionsExit):
    software: typing.Literal['dfols']
    method: typing.Literal['dfols']
    components: int

    _aposmm_sup