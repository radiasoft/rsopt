import abc
import pydantic
import typing
from functools import cached_property
from rsopt.configuration.schemas.parameters import NumericParameter, CategoryParameter, parameter_discriminator
from rsopt.configuration.schemas.settings import Setting
from rsopt.configuration.schemas.setup import Setup
from rsopt.libe_tools.executors import EXECUTION_TYPES
from rsopt import util
from rsopt import parse
from typing_extensions import Annotated

# TODO: The extra=allow is necessary with the method of dynamic parameter/setting attribute addition. But does mean
#       that extra fields a use might have put in the parameters/settings will be silently ignored here
class Code(pydantic.BaseModel, abc.ABC, extra='allow'):
    """Hold data from items in code list of the configuration.

    Internally rsopt refers to items in the code list as "Jobs" since each code will be a separate simulation
    or calculation that must be performed.

    Specific implementations of defined for each code in rsopt.codes.
    Instances of Code have parameters and settings dynamically set as attributes.
    """

    parameters: list[
        Annotated[
            typing.Union[Annotated[NumericParameter, pydantic.Tag('numeric')],
                         Annotated[CategoryParameter, pydantic.Tag('category')]
            ],
            pydantic.Discriminator(parameter_discriminator)
        ]
    ] = pydantic.Field(default_factory=list)
    settings: list[Setting] = pydantic.Field(default_factory=list)
    setup: Setup

    # TODO: Make _executor_arguments a computed_field?
    # Executor arguments are passed to libEnsemble's Executor submit command
    # Will not be set directly by user - set by the libEnsemble setup class from the info in Code
    _executor_arguments: dict

    @pydantic.field_validator('parameters', mode='before')
    @classmethod
    def format_parameters_list(cls, parsed_params: dict):
        """
        This validator transforms the list of dictionaries from the YAML format
        into a format compatible with the Pydantic model by extracting the key as 'code'.
        """
        if parsed_params:
            return [{"name": k, **v} for k, v in parsed_params.items()]
        else:
            return []

    @pydantic.field_validator('settings', mode='before')
    @classmethod
    def format_settings_list(cls, parsed_settings: dict):
        if parsed_settings:
            return [{"name": k, "value": v} for k, v in parsed_settings.items()]
        else:
            return []

    @pydantic.model_validator(mode='after')
    def set_dynamic_attributes(self):
        for param in self.parameters:
            setattr(self, param.name, param)

        for setting in self.settings:
            setattr(self, setting.name, setting)
        return self

    @pydantic.model_validator(mode='after')
    def instantiate_process_functions(self):
        for process in ('preprocess', 'postprocess'):
            if getattr(self.setup, process) is not None:
                module_path, function_name = getattr(self.setup, process)
                module = util.run_path_as_module(module_path)
                function = getattr(module, function_name)
            else:
                function = None
            setattr(self, f'get_{process}_function', function)

        return self

    @classmethod
    @abc.abstractmethod
    def serial_run_command(cls) -> str or None:
        pass

    @classmethod
    @abc.abstractmethod
    def parallel_run_command(cls) -> str or None:
        pass

    @property
    def get_sym_link_targets(self) -> set:
        return set()

    @abc.abstractmethod
    def generate_input_file(self, kwarg_dict: dict, directory: str, is_parallel: bool) -> None:
        pass

    @property
    def use_executor(self) -> bool:
        return True

    @property
    def use_mpi(self) -> bool:
        return self.setup.execution_type != EXECUTION_TYPES.SERIAL

    @property
    def run_command(self):
        if self.use_mpi:
            return self.parallel_run_command()
        return self.serial_run_command()

    @cached_property
    def input_file_model(self) -> dict or None:
        input_file_model = parse.parse_simulation_input_file(self.setup.input_file, self.code,
                                                             self.setup.ignored_files,
                                                             self.setup.execution_type == EXECUTION_TYPES.SHIFTER)
        return input_file_model
    # @property
    # def get_preprocess_function(self) -> callable or None:
    #     # set by model validator
    #     return None
    #
    # @property
    # def get_postprocess_function(self) -> callable or None:
    #     # set by model validator
    #     return None
