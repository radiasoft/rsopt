import typing
from rsopt.codes.elegant import elegant
from rsopt.configuration.schemas import setup as setup_schema
from rsopt.libe_tools.executors import EXECUTION_TYPES

class Setup(setup_schema.Setup):
    execution_type: typing.Literal[EXECUTION_TYPES.SERIAL]

class Madx(elegant.Elegant):
    code: typing.Literal['madx'] = 'madx'
    setup: Setup

    @classmethod
    def serial_run_command(cls) -> str or None:
        return 'madx'

    @classmethod
    def parallel_run_command(cls) -> str or None:
        # Execution type for madx is limited to serial by model
        return None