import enum
import pydantic

# TODO: This will go into code specific places I guess
class Elegant(enum.Enum):
    CMD = "&{command}\n"
    PARAM = "\t{field} = {value},\n"
    END = "&end\n\n"
class Spiffe(enum.Enum):
    CMD = "&{command}\n"
    PARAM = "\t{field} = {value},\n"
    END = "&end\n\n"
class Genesis(enum.Enum):
    CMD = '$newrun\n'
    PARAM = "\t{field} = {value}\n"
    END = '$end\n'

def write_command(command: pydantic.BaseModel, structure: enum.Enum) -> str:
    cmd_string = structure.CMD.value  #TODO: Support as option: .format(command=INV_MAPPING[command.__class__])
    # Iterating over __fields__ instead of directly over __fields_set__ matches the print order to the model definition which in turn matches the documentation order
    for key in command.model_fields:
        if key in command.model_fields_set:
            cmd_string += structure.PARAM.value.format(field=key, value=getattr(command, key))

    return cmd_string + structure.END.value

def write_model(model: list[pydantic.BaseModel], structure: enum.Enum) -> str:
    string_model = ""
    for m in model:
        string_model += write_command(m, structure)

    return string_model