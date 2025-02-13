import lark
import re

# TODO: Set path to resource
parser = lark.Lark.open('../../package_data/grammars/genesis.lark', g_regex_flags=re.I, rel_to=__file__)


# TODO: This follows parse function in init for now. Should unify the definitions once parsers are all converted.
def parse_simulation_input_file(input_file: str, code_name='genesis', ignored_files: list[str] or None = None,
                                shifter: bool = False) -> list[dict]:
    """Parse a genesis simulation input file.

    Args:
        input_file: (str) the path to the input file
        code_name:  (str) the name of the code. Included for compatibility.
        ignored_files: list[str] Not used. Included for compatibility.
        shifter: (bool) Not used. Included for compatibility.

    Returns:

    """
    with open(input_file, 'r') as f:
        genesis_file = f.read()
    genesis_input = parser.parse(genesis_file)

    return Transformer().transform(genesis_input)


class Transformer(lark.Transformer):
    def file(self, params):
        # return list of single command to follow structure for base_model
        cmd = {p[0]: p[1] for p in params}
        cmd['command_name'] = 'newrun'
        return {'commands': [cmd,]}
    def NAME(self, v):
        return str(v)
    def NUMBER(self, v):
        return float(v)
    def INT(self, v):
        return int(v)
    def STRING(self, v):
        return str(v).strip("\"")
    def parameter(self, param):
        k = param[0]
        if len(param[1:]) > 1:
            v = [p for p in param[1:]]
        else:
            v = param[1]
        return k, v
