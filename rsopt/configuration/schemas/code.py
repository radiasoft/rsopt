import pydantic
import typing
from rsopt.configuration.schemas.parameters import NumericParameter, CategoryParameter, parameter_discriminator
from typing_extensions import Annotated



class Code(pydantic.BaseModel, extra='allow'):
    """Hold data from items in code list of the configuration.

    Specific implementations of defined for each code in rsopt.codes.
    Instances of Code have parameters and settings dynamically set as attributes.
    """

    parameters: list[
        Annotated[
            typing.Union[Annotated[NumericParameter, pydantic.Tag('numeric')],
                         Annotated[CategoryParameter, pydantic.Tag('category')]
            ],
            pydantic.Discriminator(parameter_discriminator)
        ]
    ] = None
    settings: str  # Optional

    @pydantic.field_validator('parameters', mode='before')
    @classmethod
    def format_codes_list(cls, parsed_params: dict):
        """
        This validator transforms the list of dictionaries from the YAML format
        into a format compatible with the Pydantic model by extracting the key as 'code'.
        """
        return [{"name": k, **v} for k, v in parsed_params.items()]

    @pydantic.model_validator(mode='after')
    def set_dynamic_attributes(self):
        for param in self.parameters:
            setattr(self, param.name, param)
        return self
