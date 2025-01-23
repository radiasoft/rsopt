from rsopt.configuration.schemas.options import Options
import pydantic
import typing

class Mesh(Options):
    software = typing.Literal['mesh_scan']
    nworkers: int = 1
    mesh_file: pydantic.FilePath = ''

    use_zero_resources: bool = pydantic.Field(default=False, frozen=True)
