from rsopt.codes import spiffe

COMMAND = "&{command}\n"
PARAMETER = "\t{field} = {value},\n"
END = "&end\n\n"

def write_command(instance):
    cmd_string = COMMAND.format(command=spiffe.INV_MAPPING[instance.__class__])
    for key in instance.__fields_set__:
        cmd_string += PARAMETER.format(field=key, value=getattr(instance, key))

    return cmd_string + END


def write_model(model):
    string_model = ""
    for m in model:
        string_model += write_command(m)

    return string_model


def validate(command_list):
    model = []
    for c in command_list:
        model.append(
            spiffe.MAPPING[c['command']](**c)
        )

    return model
