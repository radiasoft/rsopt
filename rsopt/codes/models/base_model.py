import pydantic
import typing

DISCRIMINATOR_NAME = 'command_name'
T = typing.TypeVar('T')
class CommandModel(pydantic.BaseModel, typing.Generic[T]):
    commands: typing.List[T] = pydantic.Field(discriminator=DISCRIMINATOR_NAME)

    # @pydantic.model_validator(mode='after')
    # def generate_command_name_fields(self):
    #     for command in self.commands:
    #         if not hasattr(self, DISCRIMINATOR_NAME):
    #             pass


    @pydantic.validate_call
    def edit_command(self, command_name: typing.Annotated[str, pydantic.StringConstraints(to_lower=True)],
                     parameter_name: str,
                     parameter_value: typing.Any,
                     command_index: int or None = None):
        """Edit a copy of a command model and return CommandContainer with the copy.

        Args:
            command_name:
            parameter_name:
            parameter_value:
            command_index:

        Returns:

        """
        # CommandModel guarantees the model's command_name will be lower-case
        # command_name = self._sanitize_command_name(command_name)

        if command_name not in self._commands_by_name.keys():
            raise KeyError(f'Command {command_name} not found. Available commands: {self._commands_by_name.keys()}')
        assert (len(self._commands_by_name[command_name]) == 1) or (command_index is not None), \
            (f'Command {command_name} has {len(self._commands_by_name[command_name])} instances. '
             f'`command_index` must be set.')

        command_index = command_index if command_index is not None else 0

        self._commands_by_name[command_name][command_index] = (
            self._commands_by_name[command_name][command_index].model_copy(
                update={parameter_name: parameter_value}, deep=True
            )
        )

        return self


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



