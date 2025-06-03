from rsopt.configuration.schemas import options
import pydantic
import typing


class DlibOptions(options.SoftwareOptions, extra='forbid'):
    pass


class MethodDlib(options.Method):
    name: typing.Literal['dlib'] = 'dlib'
    aposmm_support = False
    local_support = False
    persis_in = ['f', 'sim_id']
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec = DlibOptions


class Dlib(options.OptionsExit):
    software: typing.Literal['dlib'] = 'dlib'
    method: typing.Union[MethodDlib] = pydantic.Field(default=MethodDlib(), discriminator='name')
    software_options: DlibOptions = pydantic.Field(default=DlibOptions())
