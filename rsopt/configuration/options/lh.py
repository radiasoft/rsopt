from rsopt.configuration.schemas import options
import pydantic
import typing


class SoftwareOptionsLH(options.SoftwareOptions):
    batch_size: int
    seed: typing.Union[int, None, typing.Literal['']] = ''


class MethodLatinHypercube(options.Method):
    name: typing.Literal['lh_scan'] = 'lh_scan'
    aposmm_support = False
    local_support = False
    persis_in = None
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float),],
    )
    option_spec = SoftwareOptionsLH


# validate_assigment is used because the outputs field may be updated after initial instantiation
class LH(options.Options, validate_assignment=True):
    software: typing.Literal['lh_scan']
    method: typing.Union[MethodLatinHypercube] = pydantic.Field(default=MethodLatinHypercube(), discriminator='name')
    software_options: SoftwareOptionsLH
    nworkers: int = 1
    outputs: list[tuple[str, type, int]] = pydantic.Field(default_factory=list)

    use_zero_resources: bool = pydantic.Field(default=False, frozen=True)

    @pydantic.model_validator(mode='after')
    def update_outputs(self):
        if len(self.outputs) > 0:
            self.method.sim_specs.static_outputs = self.outputs

        return self
