import pathlib
from ruamel.yaml import YAML


def read_configuration_file(filename: str) -> dict:
    """Read YAML file to dict.

    Args:
        filename: (str) Path to YAML file containing rsopt configuration.

    Returns: dict

    """
    return YAML(typ='safe').load(
        pathlib.Path(filename)
    )
