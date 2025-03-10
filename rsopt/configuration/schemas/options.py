import abc
import pydantic
import typing
from functools import cached_property
from rsopt import util


# TODO: This will completely replace the rsopt.configuration.options.Options
#       Options schema will also be removed

class SimSpecs(pydantic.BaseModel):
    inputs: list[str]  #  = pydantic.Field(alias='in')
    static_outputs: list[typing.Union[tuple[str, type], tuple[str, type, int]]] = pydantic.Field(default_factory=list)
    dynamic_outputs: dict[str, tuple[str, type]] = pydantic.Field(default_factory=dict)

    # _intialized_dynamic_outputs are set at run time by the Options class
    _initialized_dynamic_outputs: typing.ClassVar[list[tuple[str, type, int]]] = []

    @pydantic.computed_field
    @property
    def outputs(self) -> list:
        return list(self.static_outputs + self._initialized_dynamic_outputs)

class ExitCriteria(pydantic.BaseModel):
    sim_max: typing.Optional[int] = None
    gen_max: typing.Optional[int] = None
    wallclock_max: typing.Optional[float] = None
    stop_val: typing.Optional[tuple[str, float]] = None

class SoftwareOptions(pydantic.BaseModel, abc.ABC):
    pass

class Method(pydantic.BaseModel, abc.ABC):
    name: str
    parent_software: typing.ClassVar[str]
    aposmm_support: typing.ClassVar[bool] = pydantic.Field(..., description='Method can be used by APOSMM')
    local_support: typing.ClassVar[bool] = pydantic.Field(..., description='Method is a local optimization algorithm')
    persis_in: typing.ClassVar[list[str]] = pydantic.Field(..., description='Typing for libEnsemble persis_in')
    sim_specs: typing.ClassVar[SimSpecs] = pydantic.Field(..., description='Description of sim_specs for libEnsemble')
    option_spec: typing.ClassVar[SoftwareOptions] = pydantic.Field(..., description='Software options corresponding to this method. Used by Options validator to know what to validate against.')


# TODO: Could make Options a generic to slot in supported optimizer method types for each version
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
    load_models_at_startup: bool = False

    # TODO: This could end up being its own model
    executor_options: dict = pydantic.Field(default_factory=dict)
    use_zero_resources: bool = pydantic.Field(default=True, frozen=True, exclude=True)

    @pydantic.field_validator('method', mode='before')
    @classmethod
    def set_method_name(cls, v):
        return {'name': v}


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

    @pydantic.model_validator(mode="before")
    @classmethod
    def validate_software_options(cls, values):
        """Use method to find the expected model that defines the corresponding software_options and then validate
        user input to software_options."""
        method = values.get('method')
        software_options = values.get('software_options')
        allowed_options = cls.model_fields['method'].annotation
        valid_options = {v.model_fields['name'].default: v.option_spec for v in typing.get_args(allowed_options)}

        if method and software_options:
            expected_class = valid_options.get(method)
            if expected_class:
                if not isinstance(software_options, dict):
                    raise ValueError("software_options must be provided as a dictionary")
                values['software_options'] = expected_class(**software_options)

        return values


class OptionsExit(Options):
    exit_criteria: ExitCriteria
