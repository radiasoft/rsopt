from copy import deepcopy
from rsopt.configuration.setup.setup import SetupTemplated


def _parse_name(name):
    components = name.split('.')
    if len(components) == 3:
        field, index, name = components
    elif len(components) == 2:
        field, index, name = components[0], None, components[1]
    else:
        raise ValueError(f'Could not understand parameter/setting name {name}')

    return field, index, name


def _get_model_fields(model):
    commands = {}
    command_types = []
    elements = {}
    for i, c in enumerate(model.models.commands):
        if c['_type'] not in command_types:
            command_types.append(c['_type'])
            commands[c['_type'].lower()] = [i]
        else:
            commands[c['_type'].lower()].append(i)
    for i, e in enumerate(model.models.elements):
        elements[e['name'].upper()] = [i]

    return commands, elements

@SetupTemplated.register_setup()
class Elegant(SetupTemplated):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = None
    SERIAL_RUN_COMMAND = 'elegant'
    PARALLEL_RUN_COMMAND = 'Pelegant'
    NAME = 'elegant'

    @classmethod
    def check_setup(cls, setup):
        # Check globally required keys exist
        code = cls.NAME
        for key in cls.__REQUIRED_KEYS:
            assert setup.get(key), f"{key} must be defined in setup for {code}"
        # Validate for all keys (field in config file) are known to setup
        for key in setup.keys():
            # Can be made private if non-required code-specific fields are ever added
            if key not in (cls._KNOWN_KEYS + cls.__REQUIRED_KEYS):
                raise KeyError(f'{key} in setup block for code-type {code} is not recognized.')
        SetupTemplated.check_setup(setup)

    def _edit_input_file_schema(self, kwarg_dict):
        # Name cases in the Sirepo model:
        # eLeMENt NAmeS
        # ELEMENT TYPES
        # element parameters
        # command _type
        # command parameters

        # While exact element name case is kept at model read all elements are written to upper case. I think elegant
        # doesn't distinguish case anyway. For the element parser we'll assume element names are unique regardless of
        # case.

        commands, elements = _get_model_fields(self.input_file_model)  # modifies element name case to UPPER
        model = deepcopy(self.input_file_model)

        for n, v in kwarg_dict.items():
            field, index, name = _parse_name(n)

            if field.lower() in commands.keys():
                assert index or len(commands[field.lower()]) == 1, \
                    "{} is not unique in {}. Please add identifier".format(n, self.setup['input_file'])
                fid = commands[field.lower()][int(index) - 1 if index else 0]
                if model.models.commands[fid].get(name.lower()) is not None:
                    model.models.commands[fid][name.lower()] = v
                else:
                    command_type = model.models.commands[fid]["_type"]
                    raise NameError(f"Field: '{name}' is not found for command {command_type}")
            elif field.upper() in elements:  # Sirepo maintains element name case so we standardize to upper here
                fid = elements[field.upper()][0]
                if model.models.elements[fid].get(name.lower()) is not None:
                    model.models.elements[fid][name.lower()] = v
                else:
                    ele_type = model.models.elements[fid]["type"]
                    ele_name = model.models.elements[fid]["name"]
                    raise NameError(f"Parameter: {name} is not found for element {ele_name} with type {ele_type}")
            else:
                raise ValueError("{} was not found in the {} lattice or commands loaded from {}".format(n, self.NAME,
                                                                                            self.setup['input_file']))

        return model

    def generate_input_file(self, kwarg_dict, directory, is_parallel):
        model = self._edit_input_file_schema(kwarg_dict)

        model.write_files(directory)
