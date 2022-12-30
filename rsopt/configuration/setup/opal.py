from rsopt.configuration.setup.setup import SetupTemplated
from rsopt.configuration.setup.elegant import Elegant

@SetupTemplated.register_setup()
class Opal(Elegant):
    __REQUIRED_KEYS = ('input_file',)
    RUN_COMMAND = 'opal'
    SERIAL_RUN_COMMAND = 'opal'
    PARALLEL_RUN_COMMAND = 'opal'
    NAME = 'opal'

    @classmethod
    def _check_setup(cls, setup):
        # Check globally required keys exist
        code = cls.NAME
        for key in cls.__REQUIRED_KEYS:
            assert setup.get(key), f"{key} must be defined in setup for {code}"
        # Validate for all keys (field in config file) are known to setup
        for key in setup.keys():
            # Can be made private if non-required code-specific fields are ever added
            if key not in (cls._KNOWN_KEYS + cls.__REQUIRED_KEYS):
                raise KeyError(f'{key} in setup block for code-type {code} is not recognized.')
        SetupTemplated.check_setup(setup)
