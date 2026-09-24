import enum
from typing import Literal, Optional, Union, List
import pydantic
import numpy as np

class ParameterClasses(str, enum.Enum):
    REPEATED = "repeated"
    NUMERICAL = "numeric"
    CATEGORICAL = "category"

def parameter_discriminator(v: dict) -> str:
    """Identifies which subclass of Parameter v belongs to.

    Args:
        v: (dict)

    Returns: (str) Tag value for discriminator

    """
    if 'dimension' in v.keys():
        return ParameterClasses.REPEATED
    if 'min' in v.keys():
        return ParameterClasses.NUMERICAL
    elif 'values' in v.keys():
        return ParameterClasses.CATEGORICAL


class Parameter(pydantic.BaseModel, extra='forbid'):
    name: str = pydantic.Field(description='User specified name of the parameter. Interpreted by the `name_format` of the owning code.')
    group: Optional[Union[str, int]] = None

    def create_array(self):
        # Concrete implementations should be defined by subclasses
        pass


class NumericParameter(Parameter):
    # TODO: Type of all must match
    min: Union[int, float]
    max: Union[int, float]
    start: Union[int, float]
    # TODO: Checking requirement means looking at Options
    samples: int = 1
    scale: Union[Literal['linear'], Literal['log']] = 'linear'

    def create_array(self):
        if self.scale == 'linear':
            return np.linspace(self.min, self.max, num=self.samples)
        elif self.scale == 'log':
            return np.logspace(self.min, self.max, num=self.samples)


# Cannot subclass NumericParameter or RepeatedNumericParameter will use the min/max/start fields and not the property
# versions defined in RepeatedNumericParameter
class RepeatedNumericParameter(Parameter):
    dimension: int
    min_setting: Union[int, float] = pydantic.Field(..., alias='min')
    max_setting: Union[int, float] = pydantic.Field(..., alias='max')
    start_setting: Union[int, float] = pydantic.Field(..., alias='start')
    # TODO: Making all these have the same number of samples, could make an option to do in or list[int] to provide
    # varying numbers of samples by dimension
    samples_setting: int = pydantic.Field(1, alias='samples')
    scale: Union[Literal['linear'], Literal['log']] = 'linear'
    @property
    def min(self):
        return np.array([self.min_setting,] * self.dimension)
    @property
    def max(self):
        return np.array([self.max_setting,] * self.dimension)
    @property
    def start(self):
        return np.array([self.start_setting,] * self.dimension)
    @property
    def samples(self):
        return np.array([self.samples_setting,] * self.dimension)

    def create_array(self):
        raise NotImplementedError('MultiDimensional parameters are only supported for optimization. '
                                  'They cannot currently be used for parameter scans.')


class CategoryParameter(Parameter):
    values: List[Union[int, float, str]]

    @pydantic.computed_field(return_type=int)
    def samples(self):
        return len(self.values)

    @pydantic.computed_field(return_type=Union[int, float, str])
    def start(self):
        return self.values[0]

    def create_array(self):
        return np.array(self.values)
