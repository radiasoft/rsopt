from rsopt.configuration.schemas import options
import pydantic
import typing


class MoboOptions(pydantic.BaseModel, extra='forbid'):
    reference_point: dict[str, float]
    constraints: dict = pydantic.Field(default_factory=dict)
    num_of_objectives: int
    min_calc_to_remodel: int = 1
    use_cuda: bool = False

    @property
    def num_of_constraints(self):
        return len(self.constraints)


class MethodMobo(options.Method):
    name: typing.Literal['mobo'] = 'mobo'
    aposmm_support = False
    local_support = False
    persis_in = ['f', 'c']
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[],
        dynamic_outputs={
            'num_of_objectives': ('f', float),
            'num_of_constraints': ('c', float),
        }
    )
    option_spec = MoboOptions

class Mobo(options.OptionsExit):
    software: typing.Literal['mobo'] = 'mobo'
    method: typing.Union[MethodMobo] = pydantic.Field(MethodMobo(), discriminator='name')
    software_options: MoboOptions
