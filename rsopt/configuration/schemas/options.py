import abc
import pydantic
import typing


# TODO: This will completely replace the rsopt.configuration.options.Options
#       Options schema will also be removed

class SimSpecs(pydantic.BaseModel):
    inputs: list[str]  #  = pydantic.Field(alias='in')
    static_outputs: list[typing.Union[tuple[str, type], tuple[str, type, int]]]
    dynamic_outputs: dict[str, tuple[str, type]] = pydantic.Field(default_factory=dict)

    # _intialized_dynamic_outputs are set at run time by the Options class
    _initialized_dynamic_outputs: typing.ClassVar[list[tuple[str, type, int]]] = []

    @pydantic.computed_field
    @property
    def outputs(self) -> list:
        return list(self.static_outputs + self._initialized_dynamic_outputs)



class Method(pydantic.BaseModel, abc.ABC):
    name: str
    aposmm_support: typing.ClassVar[bool]
    local_support: typing.ClassVar[bool]
    persis_in: typing.ClassVar[list[str]]
    sim_specs: typing.ClassVar[SimSpecs]


class ExitCriteria(pydantic.BaseModel):
    sim_max: typing.Optional[int] = None
    gen_max: typing.Optional[int] = None
    elapsed_wallclock_time: typing.Optional[float] = None
    stop_val: typing.Optional[tuple[str, float]] = None


class Options(pydantic.BaseModel, abc.ABC, extra='forbid'):
    software: str
    method: Method
    nworkers: int = 2
    run_dir: str = './ensemble/'
    record_interval: int = 1
    use_worker_dirs: bool = True
    sim_dirs_make: bool = True
    output_file: str = ''
    copy_final_logs: bool = True
    sym_links: list[typing.Union[pydantic.FilePath, pydantic.DirectoryPath]] = pydantic.Field(default_factory=list)
    objective_function: tuple[pydantic.FilePath, str] = pydantic.Field(default=None)
    seed: typing.Union[None, str, int] = ''

    # TODO: This could end up being its own model
    executor_options: dict = pydantic.Field(default_factory=dict)
    use_zero_resources: bool = pydantic.Field(default=True, frozen=True)

    @pydantic.model_validator(mode='after')
    def initialize_dynamic_outputs(self):
        for param, output_type in self.method.sim_specs.dynamic_outputs.items():
            self.method.sim_specs._initialized_dynamic_outputs.append(
                output_type + (getattr(self, param),)
            )

        return self


class OptionsExit(Options):
    exit_criteria: ExitCriteria
