import pydantic
import typing
import rsopt.codes
import rsopt.configuration.options
import pydantic_core

import numpy as np

_SUPPORTED_CODES = typing.Annotated[rsopt.codes.SUPPORTED_CODES, pydantic.Field(discriminator='code')]
_SUPPORTED_SCAN_OPTIONS = rsopt.configuration.options.SUPPORTED_SAMPLE_OPTIONS
_SUPPORTED_OPTIMIZER_OPTIONS = rsopt.configuration.options.SUPPORTED_OPTIMIZE_OPTIONS

class Configuration(pydantic.BaseModel, extra='forbid'):
    codes: list[_SUPPORTED_CODES] = pydantic.Field(discriminator='code')
    options: _SUPPORTED_SCAN_OPTIONS = pydantic.Field(discriminator='software')

    # MPI Communicator fields
    comms: typing.Literal['mpi', 'local'] = pydantic.Field(default='local', exclude=True)
    mpi_size: int = pydantic.Field(default=0, exclude=True)
    is_manager: bool = pydantic.Field(default=True, exclude=True)
    mpi_comm: typing.Any = pydantic.Field(default=None, exclude=True)

    @pydantic.field_validator('codes', mode='before')
    @classmethod
    def format_codes_list(cls, parsed_data: list):
        """
        This validator transforms the list of dictionaries from the YAML format
        into a format compatible with the Pydantic model by extracting the key as 'code'.
        """
        return [{"code": key, **value} for item in parsed_data for key, value in item.items()]

    @property
    def lower_bounds(self) -> np.ndarray:
        # TODO: This is going to need handling when we have non-numeric data or require discriminating between float and int
        lower_bounds = []
        for code in self.codes:
            for param in code.parameters:
                lower_bounds.append(param.min)
        return np.array(lower_bounds)

    @property
    def upper_bounds(self) -> np.ndarray:
        # TODO: This is going to need handling when we have non-numeric data or require discriminating between float and int
        upper_bounds = []
        for code in self.codes:
            for param in code.parameters:
                upper_bounds.append(param.max)
        return np.array(upper_bounds)

    @property
    def start(self) -> list[float or int]:
        # TODO: This is going to need handling when we have non-numeric data or require discriminating between float and int
        start = []
        for code in self.codes:
            for param in code.parameters:
                start.append(param.start)
        return np.array(start)

    @property
    def dimension(self) -> int:
        dimension = 0
        for code in self.codes:
            dimension += len(code.parameters)

        return dimension

    @property
    def rsmpi_executor(self) -> bool:
        """Is rsmpi used for any Job (code)
        """
        rsmpi_used = any([c.setup.execution_type == 'rsmpi' for c in self.codes])
        return rsmpi_used

    def get_sym_link_list(self) -> list:
        # TODO: Genesis currently handles its own symlinking which is inconsistent with the usage here
        #       Should be changed to use the configuration symlink method and let libEnsemble handle

        sym_link_files = set()
        for code in self.codes:
            sym_link_files.update(code.get_sym_link_targets)
            # Each flash simulation may be a unique executable and will not be in PATH
            if code.code == 'flash':
                sym_link_files.add(code.setup.executable)
        sym_link_files.update(self.options.sym_links)

        return list(sym_link_files)

class ConfigurationOptimize(Configuration):
    options: _SUPPORTED_OPTIMIZER_OPTIONS = pydantic.Field(discriminator='software')
    @pydantic.model_validator(mode='after')
    def check_objective_function_requirement(self):
        """If the last code listed is Python and runs on the worker then an objective function is not required."""
        if self.codes[-1].code == 'python':
            if self.codes[-1].setup.serial_python_mode == 'worker':
                return self
        if self.options.objective_function is not None:
            return self

        raise pydantic_core.PydanticCustomError('objective_function_requirement',
                                                'Last code is {code} not python with python_exec_type: worker ' + \
                                                'an objective_function must be set in options: {options}.',
                                                {'code': self.codes[-1].code, 'options': self.options}
                                                )
    