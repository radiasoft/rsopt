import pydantic
import typing
import rsopt.codes
import rsopt.configuration.options
import pydantic_core

_SUPPORTED_CODES = typing.Annotated[rsopt.codes.SUPPORTED_CODES, pydantic.Field(discriminator='code')]
_SUPPORTED_OPTIONS = rsopt.configuration.options.SUPPORTED_OPTIONS

class Configuration(pydantic.BaseModel, extra='forbid'):
    codes: list[_SUPPORTED_CODES] = pydantic.Field(discriminator='code')
    options: _SUPPORTED_OPTIONS = pydantic.Field(discriminator='software')


    @pydantic.field_validator('codes', mode='before')
    @classmethod
    def format_codes_list(cls, parsed_data: list):
        """
        This validator transforms the list of dictionaries from the YAML format
        into a format compatible with the Pydantic model by extracting the key as 'code'.
        """
        return [{"code": key, **value} for item in parsed_data for key, value in item.items()]

    @pydantic.model_validator(mode='after')
    def check_objective_function_requirement(self):
        """If the last code listed is Python and runs on the worker then an objective function is not required."""
        if self.codes[-1].code == 'python':
            if self.codes[-1].python_exec_type == 'worker':
                return self
        if self.options.objective_function is not None:
            return self

        raise pydantic_core.PydanticCustomError('objective_function_requirement',
                                                'Last code is {code} not python with python_exec_type: worker ' + \
                                                'an objective_function must be set in options: {options}.',
                                                {'code': self.codes[-1].code, 'options': self.options}
                                                )
    