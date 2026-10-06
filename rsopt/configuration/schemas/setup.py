import abc
import pathlib
import pydantic
from rsopt import util
from rsopt.early_stop import EarlyStopOnError
from rsopt.libe_tools.executors import EXECUTION_TYPES


class EarlyStopSetup(pydantic.BaseModel, extra="forbid"):
    function: list[str] = pydantic.Field(min_length=2, max_length=2)
    interval: pydantic.PositiveFloat = 30.0
    on_error: EarlyStopOnError = EarlyStopOnError.RAISE

    @pydantic.field_validator("function", mode="after")
    @classmethod
    def load_function(cls, function: list[str]):
        """Resolve the module path to an absolute path and check the function can be loaded.

        The early stop function is reloaded from this path in the simulation directory at run time, so a relative
        path would not resolve there. Loading here makes a bad path or name fail before any simulation runs.
        """
        module_path, function_name = function
        module_path = pathlib.Path(module_path).resolve()
        if not module_path.is_file():
            raise ValueError(f"early_stop function file {module_path} does not exist")
        module = util.run_path_as_module(module_path)
        if not callable(getattr(module, function_name, None)):
            raise ValueError(
                f"early_stop function {function_name} was not found in {module_path}"
            )

        return [str(module_path), function_name]


class Setup(pydantic.BaseModel, abc.ABC, extra="forbid"):
    preprocess: list[str] = pydantic.Field(default=None, min_length=2, max_length=2)
    postprocess: list[str] = pydantic.Field(default=None, min_length=2, max_length=2)
    execution_type: EXECUTION_TYPES
    input_file: pydantic.FilePath
    input_distribution: str | None = None
    output_distribution: str | None = None
    cores: pydantic.PositiveInt = pydantic.Field(default=1)
    gpu: bool = False
    timeout: pydantic.PositiveFloat = pydantic.Field(default=1324512000)
    force_executor: bool = False
    ignored_files: list[str] | None = None
    shifter_image: str | None = None
    code_arguments: dict = pydantic.Field(default_factory=dict)
    environment_variables: dict = pydantic.Field(default_factory=dict)
    early_stop: EarlyStopSetup | None = None

    @pydantic.field_validator("input_file", mode="before")
    @classmethod
    def absolute_input_file_path(cls, input_file: pydantic.FilePath):
        """Make sure input_file is an absolute path.

        Used internally for rsopt to simplify loading input files into models at run time.
        """
        return pathlib.Path(input_file).resolve()
