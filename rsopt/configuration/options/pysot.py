from rsopt.configuration.schemas import options
import pydantic
import typing

class MethodPysot(options.Method):
    name: typing.Literal['pysot'] = 'pysot'
    aposmm_support = False
    local_support = False
    persis_in = ['f', 'sim_id']
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )

class PysotOptions(pydantic.BaseModel, extra='forbid'):
    num_pts: int = pydantic.Field(None, description='Sets the number of points that will be evaluated as part of the experimental planning phase before optimization begins. Defaults to 2 * (DIM + 1) if not set.')


class Pysot(options.OptionsExit):
    software: typing.Literal['pysot'] = 'pysot'
    method: typing.Union[MethodPysot] = pydantic.Field(MethodPysot(), description='name')
    software_options: PysotOptions = PysotOptions()
