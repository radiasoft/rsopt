import abc
from collections.abc import Iterable

import pydantic
import typing
from functools import cached_property
from rsopt.configuration.schemas.parameters import Parameter, NumericParameter, CategoryParameter, parameter_discriminator
from rsopt.configuration.schemas.settings import Setting
from rsopt.configuration.schemas.setup import Setup
from rsopt.libe_tools.executors import EXECUTION_TYPES
from rsopt import util
from rsopt.codes import parsers
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

    @classmethod
    def _parse_name(cls, name: str) -> dict:
        """Parse parameter/setting name for use in model editing.

        Parses rsopt's string formatting for specifying model command/element names and attributes
        `command-or-element-name.[command-or-element-attribute].[command-index]`

        Args:
            name: str

        Returns: dict

        """
        return Parameter.parse_name({'name': name})

    @abc.abstractmethod
    def generate_input_file(self, kwarg_dict: dict, directory: str, is_parallel: bool) -> None:
        pass

    @property
    def use_executor(self) -> bool:
        """Use a libEnsemble Executor for this job."""
        return True

    @property
    def use_mpi(self) -> bool:
        """Should the executor use MPI."""
        return self.setup.execution_type != EXECUTION_TYPES.SERIAL

    @property
    def run_command(self):
        """Generate the run command string to be given to the libEnsemble Executor."""
        if self.use_mpi:
            return self.parallel_run_command()
        return self.serial_run_command()

    # TODO: if parse_simulation_input_file raises an error it is not terminal and instead input_file_model is not defined
    # TODO: clean up typing as part of the Lark implementation (right now this could be dict / sirepo SimData / or maybe None)
    @cached_property
    def input_file_model(self) -> dict or None:
        input_file_model = parsers.parse_simulation_input_file(self.setup.input_file, self.code,
                                                               self.setup.ignored_files,
                                                               self.setup.execution_type == EXECUTION_TYPES.SHIFTER)
        return input_file_model

    def get_kwargs(self, x: typing.Any) -> dict:
        """Create a dictionary with parameter/setting names paired to values in iterable x.

        Pair settings and parameters in the job with concrete values that will be used in a simulation.
        Serves a mapping between the vector objects needed for most optimization / samping routines and
        structured data the user sees.

        Args:
            x: Usually an iterable (will be made Iterable if single valued). Should be equal in length
            to len(parameters) + len(settings).

        Returns: (dict)

        """
        parameters_dict = {}
        if not isinstance(x, Iterable):
            x = [x, ]
        for val, name in zip(x, [param.name for param in self.parameters]):
            parameters_dict[name] = val

        settings_dict = {s.name: s.value for s in self.settings}

        return {**parameters_dict, **settings_dict}

    def get_parameter_or_setting(self, name: str) -> Parameter or Setting:
        for item in [*self.parameters, *self.settings]:
            if item.name == name:
                return item

        raise NameError(f"{name} could not be found in Parameter or Setting lists for Code {self.code}")
