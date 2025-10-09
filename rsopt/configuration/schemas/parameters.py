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
    name: str = pydantic.Field(description='User specified name or the parameter. May include formatting to give attribute and index.')
    item_name: str = pydantic.Field('', exclude=True, description='Internal usage. Parsed name to get just the item name.')
    item_attribute: str = ''
    item_index: int = 0
    group: Optional[Union[str, int]] = None

    @pydantic.model_validator(mode="before")
    @classmethod
    def parse_name(cls, values):
        """Try to split name into item name, item attribute, item index.

        Parses rsopt's string formatting for specifying model command/element names and attributes
        `command-or-element-name.[command-or-element-attribute].[command-index]`

        If command name or element name includes '.' this formatting is not usable. As an alternative the user
        can use the item

        """
        if 'item_attribute' in values:
            assert 'item_index' in values, (f"Error for parameter {values['name']}. `item_index` must be set "
                                            f"when explicitly setting `item_attribute`")
            values['item_name'] = values['name']
            return values
        if 'name' in values:
            for part, typing in zip(values['name'].split('.'), ('item_name', 'item_attribute', 'item_index')):
                values[typing] = part

        return values

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
