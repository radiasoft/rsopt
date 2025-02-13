import logging
import typing
from copy import deepcopy
from rsopt.configuration.schemas import code
from rsopt.configuration.schemas import setup as setup_schema
from rsopt.configuration.setup import IGNORED_FIELDS

LOG = logging.getLogger('libensemble')


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

class Setup(setup_schema.Setup):
    pass

class Elegant(code.Code):
    code: typing.Literal['elegant'] = 'elegant'
    setup: Setup

    @classmethod
    def serial_run_command(cls) -> str or None:
        return 'elegant'

    @classmethod
    def parallel_run_command(cls) -> str or None:
        return 'Pelegant'

    @property
    def use_executor(self) -> bool:
        return True

    def generate_input_file(self, kwarg_dict, directory, is_parallel):
        model = self._edit_input_file_schema(kwarg_dict)

        model.write_files(directory)

    @classmethod
    def _get_ignored_fields(cls) -> dict:
        return IGNORED_FIELDS.get(cls.code, {})

    def _edit_input_file_schema(self, kwarg_dict: dict):
        # Name cases in the Sirepo model:
        # eLeMENt NAmeS
        # ELEMENT TYPES
        # element parameters
        # command _type
        # coMmaNd PaRaMetErs

        # While exact element name case is kept at model read all elements are written to upper case. I think elegant
        # doesn't distinguish case anyway. For the element parser we'll assume element names are unique regardless of
        # case.
        commands, elements = _get_model_fields(self.input_file_model)  # modifies element name case to UPPER
        model = deepcopy(self.input_file_model)

        for n, v in kwarg_dict.items():
            item_model = self.get_parameter_or_setting(n)
            field, index, name = item_model.item_name, item_model.item_index, item_model.item_attribute

            # If this is a command
            if field.lower() in commands.keys():
                # Make sure that if it is a repeated command we know which one to edit
                assert index or len(commands[field.lower()]) == 1, \
                    "{} is not unique in {}. Please add identifier".format(n, self.setup.input_file)
                if index:
                    assert int(index) <= len(commands[field.lower()]), f"Cannot assign to instance {index} of command '{field}'. There are only {len(commands[field.lower()])} instances."
                fid = commands[field.lower()][int(index) - 1 if index else 0]
                # Handle commands in a case-insensitive fashion
                if name.lower() in map(str.lower, model.models.commands[fid].keys()):  # Command fields are case-sensitive in schema so we standardize to lower
                    # If we need to edit the command now we need to match case to access dict
                    for case_name in model.models.commands[fid].keys():
                        if case_name.lower() == name.lower():
                            model.models.commands[fid][case_name] = v
                            break
                    else:
                        command_type = model.models.commands[fid]["_type"]
                        available_fields = '\nRecognized fields are:\n  ' + '\n  '.join(
                            sorted((k for k in model.models.commands[fid].keys() if
                                    not k.startswith('_') and k != 'isDisabled'))
                        )
                        raise NameError(f"Field: '{name}' is not found for command {command_type}" + available_fields)
                # The name is not recognized for this command report an error unless it is a sirepo ignored field
                # then warn the user nothing will happen
                else:
                    command_type = model.models.commands[fid]["_type"]
                    if name.lower() in self._get_ignored_fields():
                        LOG.warning("Trying to edit protected field `{name}` is not permitted.".format(name=name))
                        continue
                    available_fields = '\nRecognized fields are:\n  ' + '\n  '.join(
                        sorted((k for k in model.models.commands[fid].keys() if not k.startswith('_') and k != 'isDisabled'))
                    )
                    raise NameError(f"Field: '{name}' is not found for command {command_type}" + available_fields)
            # Assume that if the field was not a command it is an element
            elif field.upper() in elements:  # Sirepo maintains element name case so we standardize to upper here
                fid = elements[field.upper()][0]
                # Edit the element parameter - it is implied that all parameters are not case-sensitive
                if model.models.elements[fid].get(name.lower()) is not None:
                    model.models.elements[fid][name.lower()] = v
                # The element does not have the requested field, report an error to the user
                else:
                    ele_type = model.models.elements[fid]["type"]
                    ele_name = model.models.elements[fid]["name"]
                    available_parameters = '\nRecognized parameters are:\n  ' + '\n  '.join(
                        sorted((k for k in model.models.elements[fid].keys() if
                                not k.startswith('_') and k != 'isDisabled'))
                    )
                    raise NameError(f"Parameter: {name} is not found for element {ele_name} with type {ele_type}" +
                                    available_parameters)
            # The field was not a command or element we cannot handle it
            else:
                raise ValueError("{} was not found in the {} lattice or commands loaded from {}".format(field, self.code,
                                                                                            self.setup.input_file))

        return model