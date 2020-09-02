import rsopt.parse as parse
from rsopt.run import serial


def configuration(config):
    config_yaml = parse.read_configuration_file(config)
    config = parse.parse_yaml_configuration(config_yaml)

    # TODO: This is hard coded to serial for testing right now
    runner = serial(config)

    H, _, _ = runner.run()

    print(H['x'])