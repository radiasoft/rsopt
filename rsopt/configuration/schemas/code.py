import abc
import pydantic
import typing
from rsopt.configuration.schemas.parameters import NumericParameter, CategoryParameter, parameter_discriminator
from rsopt.configuration.schemas.settings import Setting
from typing_extensions import Annotated

# TODO: The extra=allow is necessary with the method of dynamic parameter/setting attribute addition. But does mean
#       that extra fields a use might have put in the parameters/settings will be silently ignored here
class Code(pydantic.BaseModel, abc.ABC, extra='allow'):
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
    ] = pydantic.Field(default_factory=list)
    settings: list[Setting] = pydantic.Field(default_factory=list)

    @pydantic.field_validator('parameters', mode='before')
    @classmethod
    def format_parameters_list(cls, parsed_params: dict):
        """
        This validator transforms the list of dictionaries from the YAML format
        into a format compatible with the Pydantic model by extracting the key as 'code'.
        """
        if parsed_params:
            return [{"name": k, **v} for k, v in parsed_params.items()]
        else:
            return []

    @pydantic.field_validator('settings', mode='before')
    @classmethod
    def format_settings_list(cls, parsed_settings: dict):
        if parsed_settings:
            print([{"name": k, "value": v} for k, v in parsed_settings.items()])
            return [{"name": k, "value": v} for k, v in parsed_settings.items()]
        else:
            return []

    @pydantic.model_validator(mode='after')
    def set_dynamic_attributes(self):
        for param in self.parameters:
            setattr(self, param.name, param)

        for setting in self.settings:
            setattr(self, setting.name, setting)
        return self

    @classmethod
    @abc.abstractmethod
    def serial_run_command(cls):
        pass

    @classmethod
    @abc.abstractmethod
    def parallel_run_command(cls):
        pass
