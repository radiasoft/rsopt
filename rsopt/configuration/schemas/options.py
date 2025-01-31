import abc
import pydantic
import typing
from functools import cached_property
from rsopt import util


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
    wallclock_max: typing.Optional[float] = None
    stop_val: typing.Optional[tuple[str, float]] = None

class SoftwareOptions(pydantic.BaseModel, abc.ABC):
    pass

class Options(pydantic.BaseModel, abc.ABC, extra='forbid'):
    software: str
    method: Method
    nworkers: int = 2
    run_dir: str = './ensemble/'
    record_interval: pydantic.PositiveInt = 0
    save_every_k_sims: int = pydantic.Field(default=1, alias='record_interval')
    use_worker_dirs: bool = True
    sim_dirs_make: bool = True
    output_file: str = ''
    copy_final_logs: bool = True
    sym_links: list[typing.Union[pydantic.FilePath, pydantic.DirectoryPath]] = pydantic.Field(default_factory=list)
    objective_function: tuple[pydantic.FilePath, str] = pydantic.Field(default=None)
    seed: typing.Union[None, str, int] = ''
    software_options: SoftwareOptions

    # TODO: This could end up being its own model
    executor_options: dict = pydantic.Field(default_factory=dict)
    use_zero_resources: bool = pydantic.Field(default=True, frozen=True, exclude=True)

    @pydantic.model_validator(mode='after')
    def initialize_dynamic_outputs(self):
        for param, output_type in self.method.sim_specs.dynamic_outputs.items():
            if hasattr(self, param):
                size = getattr(self, param)
            elif hasattr(self.software_options, param):
                size = getattr(self.software_options, param)
            else:
                raise AttributeError(f"{param} not a member of {self}")
            self.method.sim_specs._initialized_dynamic_outputs.append(
                output_type + (size,)
            )

        return self

    @cached_property
    def instantiated_objective_function(self) -> typing.Callable or None:
        if self.objective_function is not None:
            module_path, function_name = self.objective_function
            module = util.run_path_as_module(module_path)
            function = getattr(module, function_name)
            return function
        return None


class OptionsExit(Options):
    exit_criteria: ExitCriteria
