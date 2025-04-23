from rsopt.configuration.schemas import options
import pydantic
import types
import typing
import importlib
import inspect
import pkgutil

# TODO: `package` here needs to have a __path__ defined so it can't just be a module. But there appears to only
#  be type hinting for a module. Unless this a boneless wings type situation...
def find_subclasses_of_method(package: types.ModuleType):
    # Search modules in  `package` and return all classes that subclass `_target_method` but are not `_target_method`
    _target_method = options.Method
    matching_subclasses = []

    for _, module_name, _ in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, _target_method) and obj is not _target_method:
                matching_subclasses.append(obj)

    return matching_subclasses

def get_local_opt_methods():
    from rsopt.configuration import options as pkg_options
    opt_methods = find_subclasses_of_method(pkg_options)
    supported_local_opt_methods = typing.Union[tuple([m for m in opt_methods if m.aposmm_support])]

    return supported_local_opt_methods


class AposmmOptions(pydantic.BaseModel, extra='forbid'):
    initial_sample_size: int
    # max_active_runs is not required but a value will be set by Aposmm.set_default_active_runs if user does not give one
    max_active_runs: int = None
    local_opt_options: dict = None
    load_start_sample: pydantic.FilePath = None
    # dist_to_bound_multiple: float =
    # lhs_divisions
    # mu
    # nu
    # rk_const
    # stop_after_k_minima
    # stop_after_k_runs

    @pydantic.model_validator(mode='after')
    @classmethod
    def validate_local_opt_options(cls, v, validation_info):
        # Needs to be run after because the method info will not be validated
        # and thus will not be in validation_info if run in mode=before

        model = validation_info.data['method'].option_spec
        v.local_opt_options = model.model_validate(v.local_opt_options)

        return v


class Aposmm(options.OptionsExit):
    software: typing.Literal['aposmm'] = 'aposmm'
    method: get_local_opt_methods() = pydantic.Field(discriminator='name')
    software_options: AposmmOptions

    @pydantic.model_validator(mode='after')
    def set_default_active_runs(self) -> 'Base':
        # This validator needs to run after 'nworkers' and 'software_options' fields
        # are validated because it checks their values

        if self.software_options.max_active_runs is None:
            calculated_runs = self.nworkers - 1

            if calculated_runs <= 0:
                raise ValueError(
                    f"Default 'max_active_runs' ({calculated_runs}) calculated from "
                    f"'workers' ({self.workers}) must be non-negative (>= 0)."
                )
            self.software_options.max_active_runs = calculated_runs

        # Important: Always return the validated model instance (self) from the validator
        return self

    @pydantic.model_validator(mode='after')
    def initialize_dynamic_outputs(self):
        for param, output_type in self.method.sim_specs.dynamic_outputs.items():
            if hasattr(self, param):
                size = getattr(self, param)
            elif hasattr(self.software_options.local_opt_options, param):
                size = getattr(self.software_options, param)
            else:
                raise AttributeError(f"{param} not a member of {self}")
            self.method.sim_specs._initialized_dynamic_outputs.append(
                output_type + (size,)
            )

        return self

    @pydantic.model_validator(mode="before")
    @classmethod
    def validate_software_options(cls, values):
        """This validator normally handles picking the software_options model based on the method field.
           However, the method cannot easily be generalized to account for aposmm. Since we only have one software_options
           model for aposmm it is easiest just ot skip this validator in this case."""

        return values
