import enum
import pathlib
import pydantic
from rsopt.codes.models import base_model

# TODO: This will go into code specific places I guess
class Elegant(enum.Enum):
    CMD = "&{command_name}\n"
    PARAM = "\t{field} = {value},\n"
    END = "&end\n\n"
class Spiffe(enum.Enum):
    CMD = "&{command_name}\n"
    PARAM = "\t{field} = {value},\n"
    END = "&end\n\n"
class Genesis(enum.Enum):
    CMD = '$newrun\n'
    PARAM = "\t{field} = {value}\n"
    END = '$end\n'

def write_command(command: pydantic.BaseModel, structure: enum.Enum) -> str:
    cmd_string = structure.CMD.value.format(**{'command_name': command.command_name, **command.model_dump()})

    for key, value in command.model_dump(exclude_defaults=True).items():
        cmd_string += structure.PARAM.value.format(field=key, value=value)

    return cmd_string + structure.END.value

def write_model(model: base_model.CommandModel, structure: enum.Enum) -> str:
    string_model = ""
    for m in model.commands:
        string_model += write_command(m, structure)

    return string_model

def write_to_file(model_string: str, filename: str, path: str = '.') -> None:
    filepath = pathlib.Path(path) / filename
    with open(filepath, "w") as f:
        f.write(model_string)

# TODO: Should have a write to file function defined
# TODO: Will need to handle supporting file linking or writing
