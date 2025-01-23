import pydantic
import typing
import rsopt.codes

_SUPPORTED_CODES = typing.Annotated[rsopt.codes.SUPPORTED_CODES, pydantic.Field(discriminator='code')]

class Configuration(pydantic.BaseModel):
    codes: list[_SUPPORTED_CODES] = pydantic.Field(discriminator='code')
    software: OPTIONS = pydantic.Field(discriminator='software')


    @pydantic.field_validator('codes', mode='before')
    @classmethod
    def format_codes_list(cls, parsed_data: list):
        """
        This validator transforms the list of dictionaries from the YAML format
        into a format compatible with the Pydantic model by extracting the key as 'code'.
        """
        return [{"code": key, **value} for item in parsed_data for key, value in item.items()]
    