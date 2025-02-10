from rsopt.codes.parsers import spiffe_parser
from rsopt.codes.models import spiffe_model, base_model
from rsopt.codes.writers import write

parser = spiffe_parser.parser
with open('gun.spiffe', 'r') as f:
    spiffe_file = f.read()

spiffe_input = parser.parse(spiffe_file)
test_model = base_model.generate_model(spiffe_model.SPIFFE, 'spiffe')

spiffe_model_instance = test_model.model_validate(
    spiffe_parser.Transformer().transform(spiffe_input)
)
print(spiffe_model_instance)

spiffe_model_instance.edit_command(command_name='define_geometry',
                                   parameter_name='nz',
                                   parameter_value=264,
                                   command_index=0
                                   )

print('updated spiffe model', spiffe_model_instance)
