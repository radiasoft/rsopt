from typing import Any, Optional, Union, List
import pydantic

class Parameter(pydantic.BaseModel):
    name: str
    type: str = 'numeric'

class NumericParameter(pydantic.BaseModel):
    # TODO: Type of all must match
    min: Union[int, float]
    max: Union[int, float]
    start: Union[int, float]
    # TODO: Checking requirement means looking at Options
    samples: Optional[int] = 1
    scale: Optional[]

class CategoryParameter(pydantic.BaseModel):
    values: List[Union[int, float, str]]
