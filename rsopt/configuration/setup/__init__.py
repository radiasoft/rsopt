from libensemble.executors import MPIExecutor
from rsopt.libe_tools.executors import register_rsmpi_executor


EXECUTION_TYPES = {'serial': MPIExecutor,  # Serial jobs executed in the shell use the MPIExecutor for simplicity
                    'parallel': MPIExecutor,
                    'rsmpi': register_rsmpi_executor,
                    'shifter': MPIExecutor}


def iter_setup_dict(setup: dict):
    for name, values in setup.items():
        yield name, values


_SETUP_READERS = {
    dict: iter_setup_dict
}
