import pathlib
from ruamel.yaml import YAML
from rsopt.configuration.schemas import configuration
from rsopt.configuration.options import SUPPORTED_OPTIONS

def _config_discriminator(v: configuration._ThinConfiguration) -> str:
    if v.software in SUPPORTED_OPTIONS.get_sample_names():
        return 'sample'
    elif v.software in SUPPORTED_OPTIONS.get_optimize_names():
        return 'optimize'


def read_configuration_file(filename: str) -> dict:
    """Read YAML file to dict.

    Args:
        filename: (str) Path to YAML file containing rsopt configuration.

    Returns: dict

    """
    return YAML(typ='safe').load(
        pathlib.Path(filename)
    )

def parse_sample_configuration(config_dict: dict) -> configuration.ConfigurationSample:
    return configuration.ConfigurationSample.model_validate(config_dict)


def parse_optimize_configuration(config_dict: dict) -> configuration.ConfigurationOptimize:
    return configuration.ConfigurationOptimize.model_validate(config_dict)


def parse_unknown_configuration(config_dict: dict) -> configuration.ConfigurationSample or configuration.ConfigurationOptimize:
    _thin_config = configuration._ThinConfiguration.model_validate(config_dict)
    _config = {
        'sample': configuration.ConfigurationSample,
        'optimize': configuration.ConfigurationOptimize,
    }[_config_discriminator(_thin_config)]

    return _config.model_validate(config_dict)
