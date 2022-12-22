from rsopt.configuration.setup.setup import SetupTemplated
from rsopt.configuration.setup.elegant import Elegant

@SetupTemplated.register_setup()
class Madx(Elegant):
    __REQUIRED_KEYS = ('input_file', )
    RUN_COMMAND = 'madx'
    SERIAL_RUN_COMMAND = 'madx'
    # MAD-X does not support parallel execution. However, setting PARALLEL_RUN_COMMAND allows MAD-X
    # to work when the force_executor option is invoked. Parallel execution will be stopped by Madx._check_setup.
    PARALLEL_RUN_COMMAND = 'madx'
    NAME = 'madx'

    @classmethod
    def _check_setup(cls, setup):
        Elegant._check_setup(setup)

        # MAD-X is serial only
        execution_type = setup.get('execution_type')
        assert execution_type == 'serial', f"`execution_type: {execution_type}` not supported for madx." \
                                           f" Must use `execution_type: serial`"

