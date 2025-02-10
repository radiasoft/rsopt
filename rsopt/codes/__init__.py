import pydantic
import typing
from rsopt.codes import spiffe, elegant, python, opal, madx, flash, genesis
# Templated codes have schema files that can be used to check input and create run files. Otherwise user
#   must supply module containing inputs
TEMPLATED_CODES = ['elegant', 'opal', 'madx', 'flash']

# Parser to allow sirepo to initiate
SIREPO_SIM_TYPES = ['elegant', 'opal', 'madx', 'genesis']

# Supported codes have defined Job class
# FUTURE: 'Unsupported' codes could become a class of supported codes that have expanded user input required to run
# SUPPORTED_CODES = ['python', 'user', 'genesis', *TEMPLATED_CODES]

SUPPORTED_CODES = typing.Union[elegant.Elegant, flash.Flash, genesis.Genesis,
                               madx.Madx, opal.Opal,  python.Python, spiffe.Spiffe]


# TODO: Create model will get a list of dictionaries containing the parsed file values. Need to map the inputs
#  to the appropriate Models for validation and processing. So the question is how to idenfity/mark the dictionaries
#  so they map to the appropriate Model.

def create_model(command_list: list[dict], command_mapping: dict) -> list[BaseModel]:
    model = []

    for c in command_list:
        model.append(
            command_mapping[c['command']](**c)
        )

    return model
