import pydantic
import typing

class Setting(pydantic.BaseModel):
    name: str
    item_name: str = pydantic.Field('', exclude=True, description='Internal usage. Parsed name to get just the item name.')
    item_attribute: str = ''
    item_index: int = 0
    value: typing.Any

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
