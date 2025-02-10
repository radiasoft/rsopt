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
