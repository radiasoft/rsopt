import abc
import pydantic
import typing


# TODO: This will completely replace the rsopt.configuration.options.Options
#       Options schema will also be removed

class Options(pydantic.BaseModel, abc.ABC):
    nworkers: int = 2
    run_dir: str = './ensemble/'
    record_interval: int = 1
    use_worker_dirs: bool = True
    sim_dirs_make: bool = True
    output_file: str = ''
    copy_final_logs: bool = True
    sym_links: list[typing.Union[pydantic.FilePath, pydantic.DirectoryPath]] = pydantic.Field(default_factory=list)
    objective_function: tuple[pydantic.FilePath, str]
    seed: typing.Union[None, str, int] = ''

    # TODO: This could end up being its own model
    executor_options: dict = pydantic.Field(default_factory=dict)
    use_zero_resources: bool = pydantic.Field(default=True, frozen=True)

    # Class Variables
    # TODO: software and/or methods as  an enum?
    _software = typing.ClassVar[str]
    _method = typing.ClassVar[Method]
    _type = typing.ClassVar[str]
    _methods = typing.ClassVar[list[str]]

    @pydantic.field_validator('method', mode='after')
    def set_outputs_size(self, v):
        """Some sim specs require a size set at initialization."""
        for output in v:
            if len(output) == 3:
                if getattr(self, output[2]):
                    setattr(self, output[2], getattr(self, output[2]))


class SimSpecs(pydantic.BaseModel):
    inputs: list[str] = pydantic.Field(alias='in')
    outputs: list[list[str]]


class Method(pydantic.BaseModel, abc.ABC):
    name: str
    aposmm_support: typing.ClassVar[bool]
    local_support: typing.ClassVar[bool]
    persis_in: typing.ClassVar[list[str]]
    sim_specs: typing.ClassVar[SimSpecs]


class ExitCriteria(pydantic.BaseModel):
    sim_max: typing.Optional[int]
    gen_max: typing.Optional[int]
    elapsed_wallclock_time: typing.Optional[float]
    stop_val: typing.Optional[tuple[str, float]]


class OptionsExit(Options):
    exit_criteria: ExitCriteria

    """
  software_options:
    typing:
      - dict
  method:
    typing:
      - str
    """
