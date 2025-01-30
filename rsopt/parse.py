import pathlib
from ruamel.yaml import YAML
from rsopt.configuration.schemas import configuration

def read_configuration_file(filename: str) -> dict:
    """Read YAML file to dict.

    Args:
        filename: (str) Path to YAML file containing rsopt configuration.

    Returns: dict

    """
    return YAML(typ='safe').load(
        pathlib.Path(filename)
    )

def parse_sample_configuration(config_dict: dict) -> configuration.Configuration:
    return configuration.Configuration.model_validate(config_dict)

def parse_optimize_configuration(config_dict: dict) -> configuration.ConfigurationOptimize:
    return configuration.ConfigurationOptimize.model_validate(config_dict)
