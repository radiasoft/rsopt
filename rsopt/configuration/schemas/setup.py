import abc
import pathlib
import pydantic
from rsopt.libe_tools.executors import EXECUTION_TYPES


class Setup(pydantic.BaseModel, abc.ABC, extra='forbid'):
    preprocess: list[str] = pydantic.Field(default=None, min_length=2, max_length=2)
    postprocess: list[str] = pydantic.Field(default=None, min_length=2, max_length=2)
    execution_type: EXECUTION_TYPES
    input_file: pydantic.FilePath
    input_distribution: str = None  # TODO: could be a delayed validation against previous code (might be too hard to be worth it)
    output_distribution: str = None
    cores: pydantic.PositiveInt = pydantic.Field(default=1)
    timeout: pydantic.PositiveFloat = pydantic.Field(default=1324512000)
    force_executor: bool = False
    ignored_files: list[str] = None
    shifter_image: str = None
    code_arguments: dict = pydantic.Field(default_factory=dict)
    environment_variables: dict = pydantic.Field(default_factory=dict)

    @pydantic.field_validator('input_file', mode='before')
    @classmethod
    def absolute_input_file_path(cls, input_file: pydantic.FilePath):
        """Make sure input_file is an absolute path.

         Used internally for rsopt to simplify loading input files into models at run time.
        """
        return pathlib.Path(input_file).resolve()



