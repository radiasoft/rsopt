import typing
from typing import Any, Optional, Union, List
import pydantic

def parameter_discriminator(v: dict) -> str:
    """Identifies which subclass of Parameter v belongs to.

    Args:
        v: (dict)

    Returns: (str) Tag value for discriminator

    """
    if 'min' in v.keys():
        return 'numeric'
    elif 'values' in v.keys():
        return 'category'


class Parameter(pydantic.BaseModel):
    name: str = pydantic.Field(description='User specified name or the parameter. May include formatting to give attribute and index.')
    item_name: str = pydantic.Field('', exclude=True, description='Internal usage. Parsed name to get just the item name.')
    item_attribute: str = ''
    item_index: int = 0
    group: Optional[str or int] = None

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


class NumericParameter(Parameter):
    # TODO: Type of all must match
    min: Union[int, float]
    max: Union[int, float]
    start: Union[int, float]
    # TODO: Checking requirement means looking at Options
    samples: Optional[int] = 1
    scale: Union[typing.Literal['linear'], typing.Literal['log']] = 'linear'

class CategoryParameter(Parameter):
    values: List[Union[int, float, str]]
