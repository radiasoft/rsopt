import pydantic
import typing

class Setting(pydantic.BaseModel):
    name: str
    value: typing.Any
