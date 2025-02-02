import lark
import re

# TODO: Set path to resource
parser = lark.Lark.open('../package_data/grammars/genesis.lark', g_regex_flags=re.I, rel_to=__file__)

class Transformer(lark.Transformer):
    def file(self, params):
        for p in params:
            print(p, len(p))
        return {p[0]: p[1] for p in params}
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
