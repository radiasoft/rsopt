from rsopt.configuration.schemas import options
import pydantic
import typing

class MethodDfols(options.Method):
    name: typing.Literal['dfols']
    aposmm_support = True
    local_support = True
    persis_in = ['f', 'fvec']
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={
            'components': ('fvec', float)
        }
    )

class DfolsOptions(options.SoftwareOptions, extra='allow'):
    components: int

class Dfols(options.OptionsExit):
    software: typing.Literal['dfols']
    method: typing.Union[MethodDfols] = pydantic.Field(default=MethodDfols, discriminator='name')
    software_options: DfolsOptions


def get_required_fields(model):
    return [field_name for field_name, field in model.__fields__.items() if field.required]
