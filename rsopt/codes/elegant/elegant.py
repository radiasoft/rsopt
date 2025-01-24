import typing
from rsopt.configuration.schemas import code
from rsopt.configuration.schemas import setup as setup_schema

class Setup(setup_schema.Setup):
    madeup_requirement: str

class Elegant(code.Code):
    code: typing.Literal['elegant']
    setup: Setup
