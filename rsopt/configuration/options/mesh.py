from rsopt.configuration.schemas import options
import pydantic
import typing

class MethodMeshScan(options.Method):
    name: typing.Literal['mesh_scan'] = 'mesh_scan'
    aposmm_support = False
    local_support = False
    persis_in = None
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float),],
    )

class SoftwareOptionsMesh(options.SoftwareOptions):
    sampler_repeats: pydantic.PositiveInt = pydantic.Field(default=1, gt=0)
    mesh_file: pydantic.FilePath = ''

class Mesh(options.Options, validate_assignment=True):
    # validate_assigment is used because the outputs field may be updated after initial instantiation
    software: typing.Literal['mesh_scan']
    method: typing.Union[MethodMeshScan] = pydantic.Field(default=MethodMeshScan(name='mesh_scan'), discriminator='name')
    software_options: SoftwareOptionsMesh = SoftwareOptionsMesh()
    nworkers: int = 1
    outputs: list[tuple[str, type, int]] = pydantic.Field(default_factory=list)

    use_zero_resources: bool = pydantic.Field(default=False, frozen=True)

    @pydantic.model_validator(mode='after')
    def update_outputs(self):
        if len(self.outputs) > 0:
            self.method.sim_specs.static_outputs = self.outputs

        return self
