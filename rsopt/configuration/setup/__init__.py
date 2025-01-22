from enum import Enum
from libensemble.executors import MPIExecutor, Executor
from rsopt.libe_tools.executors import register_rsmpi_executor

class EXECUTION_TYPES(Enum):
    SERIAL = 'serial'
    PARALLEL = 'parallel'
    RSMPI = 'rsmpi'
    SHIFTER = 'shifter'

    def __init__(self, exec_type):
        self.exec_type = exec_type

        self._map = {'serial': Executor,
                     'parallel': MPIExecutor,
                     'rsmpi': register_rsmpi_executor,
                     'shifter': MPIExecutor
        }

    @property
    def exec_obj(self):
        return self._map[self.exec_type]

def iter_setup_dict(setup: dict):
    for name, values in setup.items():
        yield name, values


SETUP_READERS = {
    dict: iter_setup_dict
}

# Ignored fields in sirepo schema that rsopt editor should check for - keyed by code name
IGNORED_FIELDS = {
    'elegant': [
                "mpi_io_write_buffer_size",
                "rootname",
                "search_path",
                "semaphore_file"
    ],
}
