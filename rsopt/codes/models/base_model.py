import pydantic
import typing

DISCRIMINATOR_NAME = 'command_name'
T = typing.TypeVar('T')
class CommandModel(pydantic.BaseModel, typing.Generic[T]):
    commands: typing.List[T] = pydantic.Field(discriminator=DISCRIMINATOR_NAME)


    # Use a model_validator to distribute from the command list to command fields by name
    # This method mean each command-name field and 'commands' will contain lists pointing to common objects
    # allowing the edit_command to only search and edit in one place
    @pydantic.model_validator(mode='after')
    def generate_command_name_fields(self):
        for command in self.commands:
            # CommandModel will have a field, that is a list,  corresponding to each command name type
            # add each command model instance to the field corresponding to its name
            getattr(self, getattr(command, DISCRIMINATOR_NAME)).append(command)

        return self


    @pydantic.validate_call
    def edit_command(self, command_name: typing.Annotated[str, pydantic.StringConstraints(to_lower=True)],
                     parameter_name: str,
                     parameter_value: typing.Any,
                     command_index: int or None = None) -> None:
        """Edit a copy of a command model and return CommandContainer with the copy.

        Args:
            command_name: (str) Name of the command type to edit.
            parameter_name: (str) Name of the parameter to edit.
            parameter_value: (typing.Any) New value of the parameter.
            command_index: (int) Index of the command to edit, required if the command is used multiple times.

        Returns:

        """
        command_list = getattr(self, command_name)
        assert (len(command_list) == 1) or (command_index is not None), \
            (f'Command {command_name} has {len(command_list)} instances. '
             f'`command_index` must be set.')

        command_index = command_index if command_index is not None else 0

        setattr(command_list[command_index], parameter_name, parameter_value)


def generate_model(model_T, code_name):
    model_type = typing.Annotated[model_T, pydantic.Field(discriminator=DISCRIMINATOR_NAME)]
    base_model = CommandModel[model_type]

    model_name = f"{code_name}Model"

    dynamic_fields = {}
    for m in typing.get_args(model_T):
        _field = pydantic.Field(default_factory=list, discriminator=DISCRIMINATOR_NAME)
        dynamic_fields[m.model_fields[DISCRIMINATOR_NAME].default] = (list[m], _field)

    dynamic_model = pydantic.create_model(model_name, __base__=base_model, **dynamic_fields)

    return dynamic_model



