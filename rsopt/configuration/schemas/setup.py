import abc
import pydantic
from rsopt.configuration import setup

# TODO: Right now this just provides the basic validation of inputs from the config file
#       the plan is to hand this over to the existing rsopt.configuration.setup to be used as normal
#       In the future it could be useful to consider folding rsopt.configuration.setup classes into the pydantic models

class Setup(pydantic.BaseModel, abc.ABC):
    preprocess: list[str] = pydantic.Field(default=None, min_length=2, max_length=2)
    postprocess: list[str] = pydantic.Field(default=None, min_length=2, max_length=2)
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
