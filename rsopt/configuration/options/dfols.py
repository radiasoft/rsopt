from rsopt.configuration.schemas import options
import pydantic
import typing


class DfolsOptions(options.SoftwareOptions, extra='allow'):
    components: int


class MethodDfols(options.Method):
    name: typing.Literal['dfols'] = 'dfols'
    parent_software = 'dfols'
    aposmm_support = True
    local_support = True
    persis_in = ['f', 'fvec']
    sim_specs = options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={
            'components': ('fvec', float)
        }
    )
    option_spec = DfolsOptions

class Dfols(options.OptionsExit):
    software: typing.Literal['dfols']
    method: typing.Union[MethodDfols] = pydantic.Field(default=MethodDfols(), discriminator='name')
    software_options: DfolsOptions
