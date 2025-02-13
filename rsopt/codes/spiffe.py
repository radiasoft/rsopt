import pathlib
import typing
from functools import cached_property
from rsopt.codes.models import base_model, spiffe_model
from rsopt.codes.parsers import spiffe_parser
from rsopt.codes.writers import write
from rsopt.configuration.schemas import code
from rsopt.configuration.schemas import setup as setup_schema

class Setup(setup_schema.Setup):
    pass

class Spiffe(code.Code):
    code: typing.Literal['spiffe'] = 'spiffe'
    setup: Setup

    @classmethod
    def serial_run_command(cls) -> str or None:
        return 'spiffe'

    @classmethod
    def parallel_run_command(cls) -> str or None:
        return 'spiffe'

    def generate_input_file(self, kwarg_dict: dict, directory: str, is_parallel: bool) -> None:
        # There are only commands so this is simpler than some other tracking code cases
        spiffe_model_instance = self.input_file_model.model_copy(deep=True)

        for name, value in kwarg_dict.items():
            item_model = self.get_parameter_or_setting(name)
            spiffe_model_instance.edit_command(command_name=item_model.item_name,
                                               parameter_name=item_model.item_attribute,
                                               parameter_value=value,
                                               command_index=item_model.item_instance
                                               )
        # TODO: Right now we don't handle linking of resources like the geometry file. User will need to do that in rsopt config
        write.write_to_file(
            write.write_model(spiffe_model_instance, write.Spiffe),
            filename=self.setup.input_file.name,
            path=directory
        )

    @cached_property
    def input_file_model(self) -> base_model.CommandModel:
        input_file_model = spiffe_parser.parse_simulation_input_file(self.setup.input_file, self.code,None,False)

        model_schema = base_model.generate_model(spiffe_model.SPIFFE, 'spiffe')

        return model_schema.model_validate(input_file_model)
