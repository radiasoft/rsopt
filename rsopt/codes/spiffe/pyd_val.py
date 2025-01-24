from typing import Any, Optional
from pydantic import BaseModel, Field

class CommentedField(BaseModel):
    value: Any
    commented: bool = False
    original_value: Optional[Any] = None

class ExampleCommand(BaseModel):
    param1: CommentedField = Field(default_factory=lambda: CommentedField(value=0))
    param2: CommentedField = Field(default_factory=lambda: CommentedField(value="default"))
    param3: CommentedField = Field(default_factory=lambda: CommentedField(value=None))


def parse_text_file(file_path: str):
    commands = []
    with open(file_path, "r") as file:
        current_command = None
        parsed_params = {}

        for line in file:
            line = line.strip()

            # Ignore empty lines
            if not line:
                continue

            # Detect command headers
            if line.startswith("[") and line.endswith("]"):
                # Save the previous command if any
                if current_command:
                    commands.append((current_command, parsed_params))
                current_command = line.strip("[]")
                parsed_params = {}
                continue

            # Detect comments
            is_commented = line.startswith("#")
            line = line.lstrip("#").strip()  # Remove comment marker for processing

            if "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                parsed_params[key] = {
                    "value": value,
                    "commented": is_commented,
                }

        # Finalize the last command
        if current_command:
            commands.append((current_command, parsed_params))

    return commands

def instantiate_models(parsed_commands, schema_mapping):
    models = {}

    for command_name, params in parsed_commands:
        schema = schema_mapping.get(command_name)
        if not schema:
            raise ValueError(f"Unknown command: {command_name}")

        model_data = {}
        for field_name, field_info in schema.__fields__.items():
            field_default = field_info.default_factory()  # Use default factory for `CommentedField`
            param_data = params.get(field_name, {"value": field_default.value, "commented": False})

            # Construct the CommentedField instance
            model_data[field_name] = CommentedField(
                value=param_data["value"] if not param_data["commented"] else field_default.value,
                commented=param_data["commented"],
                original_value=param_data["value"] if param_data["commented"] else None,
            )

        # Instantiate the model
        models[command_name] = schema(**model_data)

    return models

def serialize_model(model: BaseModel):
    serialized_data = {}
    for field_name, field_value in model.dict().items():
        serialized_data[field_name] = field_value["value"]
    return serialized_data

# Mapping of command names to Pydantic schemas
schema_mapping = {
    "ExampleCommand": ExampleCommand,
}

# Parse and instantiate

with open("commands.txt", 'w') as file:
    file.write("""[ExampleCommand]
param1 = 42
# param2 = commented out
param3 = 3.14
    """)

parsed_commands = parse_text_file("commands.txt")
models = instantiate_models(parsed_commands, schema_mapping)

# Print models
for command_name, model in models.items():
    print(f"Model for {command_name}: {model}")
    print(f"Serialized {command_name}: {serialize_model(model)}")

