import pydantic
from rsopt.configuration import setup

class Setup(pydantic.BaseModel):
    preprocess: list[str, str] = None
    postprocess: list[str, str] = None
    execution_type: setup.EXECUTION_TYPES
    input_file: str
    input_distribution: str = None  # TODO: could be a delayed validation against previous code (might be too hard to be worth it)
    output_distribution: str = None
    cores: pydantic.PositiveInt = pydantic.Field(default=1)
    timeout: pydantic.PositiveFloat = pydantic.Field(default=None)
    force_executor: bool = False
    ignored_files: list[str] = None
    shifter_image: str = None
    code_arguments: dict = pydantic.Field(default_factory=dict)
    environment_variables: dict = pydantic.Field(default_factory=dict)
