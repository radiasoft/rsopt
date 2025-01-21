from typing import Any, Optional, Union, List
import pydantic

def parameter_discriminator(v: dict) -> str:
    if v.get('min'):
        return 'numeric'
    elif v.get('values'):
        return 'category'

class Parameter(pydantic.BaseModel):
    name: str
    group: Optional[str or int] = None

class NumericParameter(Parameter):
    # TODO: Type of all must match
    min: Union[int, float]
    max: Union[int, float]
    start: Union[int, float]
    # TODO: Checking requirement means looking at Options
    samples: Optional[int] = 1
    # scale: Optional[]

class CategoryParameter(Parameter):
    values: List[Union[int, float, str]]
