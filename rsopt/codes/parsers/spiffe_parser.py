import lark
import re

# TODO: Set path to resource
parser = lark.Lark.open('../../package_data/grammars/spiffe.lark', g_regex_flags=re.I, rel_to=__file__)

class Transformer(lark.Transformer):
    def __init__(self):
        self._macros = {}
        self._rpn = {}
        self._cmd = {}

        self._defer_rpn = True
        self._defer_cmd = True

    def NEWLINE(self, token):
        return lark.Discard

    def ESCAPED_RPN_START(self, token):
        return lark.Discard

    def ESCAPED_RPN_END(self, token):
        return lark.Discard

    def ESCAPED_SHELL_START(self, token):
        return lark.Discard

    def ESCAPED_SHELL_END(self, token):
        return lark.Discard

    def SHELL_CONTENT(self, token):
        self._cmd[token] = token
        return '"{' + self._cmd[token] + '}"'

    def RPN_CONTENT(self, token):
        self._rpn[token] = token
        return '"(' + self._rpn[token] + ')"'

    def command_name(self, token):
        return str(token)

    def command_end(self, token):
        return lark.Discard

    def start(self, cmds):
        command_list = [cmd for cmd in cmds if cmd]

        command_data = {}

        command_data['commands'] = command_list
        return command_data # [cmd for cmd in cmds if cmd]

    def valid_command(self, cmd):
        cmd_name = cmd[0]
        cmd_parameters = cmd[1] if len(cmd) > 1 else []
        # TODO: OK to import rsopt.codes.models.base_model.DISCRIMINATOR_NAME?
        return {'command_name': cmd_name, **{k: v for (k, v) in cmd_parameters}}

    def ignore(self, cmd):
        return

    def parameter_list(self, plist):
        return list(plist)

    def parameter(self, param):
        k, v = param
        return k, v

    def NAME(self, w):
        return str(w)

    def numbers(self, n):
        (n,) = n
        return float(n)

    def string(self, s):
        (s,) = s
        return str(s)

    def shell_cmd(self, cmd):
        (cmd,) = cmd
        return cmd

    def rpn_expression(self, rpn):
        (rpn,) = rpn
        return rpn