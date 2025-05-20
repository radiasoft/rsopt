import os
import logging
import pathlib
from enum import Enum
from libensemble.executors.mpi_executor import MPIExecutor, Executor
from ruamel.yaml import YAML
from rsopt import EXECUTOR_SCHEMA

EXECUTOR_SCHEMA = YAML().load(pathlib.Path(EXECUTOR_SCHEMA))
logger = logging.getLogger(__name__)
# To change logging level for just this module
# logger.setLevel(logging.DEBUG)

_RSMPI_CONFIG_PATH = EXECUTOR_SCHEMA['rsmpi']['config_path']
_DEFAULT_SHIFTER_IMAGE = 'radiasoft/sirepo:prod'

def register_rsmpi_executor(hosts: str or list = 'auto') -> MPIExecutor:
    """
    Create an MPIExecutor that can use rsmpi. The executor is returned and may be used to register calculations
    for workers like any other libEnsemble executor.
    :param hosts: (str or list) If 'auto' then all rsmpi resources are detected and used. If a list is given
                                the list entries are written to the libe_nodes file.

    :return: libensemble.executors.mpi_executor.MPIExecutor object
    """
    schema = EXECUTOR_SCHEMA['rsmpi']

    if type(hosts) == list:
        pass
    elif hosts == 'auto':
        hosts = _detect_rsmpi_resources()
    else:
        raise TypeError('hosts must be str or int')

    _generate_rsmpi_node_file(hosts)

    customizer = {k:  schema[k] for k in ('mpi_runner', 'runner_name', 'subgroup_launch')}
    jobctrl = MPIExecutor(custom_info=customizer)
    # Set longer fail time - rsmpi is relatively slow to start
    jobctrl.fail_time = schema['fail_time']
    
    return jobctrl


def _detect_rsmpi_resources() -> int:
    hosts = 0
    assert os.path.isfile(_RSMPI_CONFIG_PATH), "rsmpi configuration does not exist"
    with open(_RSMPI_CONFIG_PATH, 'r') as ff:
        for line in ff.readlines():
            if 'Host' in line:
                hosts += 1

    assert hosts > 0, 'No hosts listed in rsmpi configuration'

    return hosts


def _generate_rsmpi_node_file(nodes: int or list) -> None:
    with open('libe_nodes', 'w') as ff:
        if type(nodes) == int:
            for node in range(1, nodes+1):
                ff.write(str(node)+'\n')
        elif type(nodes) == list:
            for node in nodes:
                ff.write(str(node)+'\n')
        else:
            raise TypeError(f'nodes must be int or list. Received instead: {nodes}')


def format_task_string(job: "import rsopt.configuration.schemas.code") -> str:
    shifter_command = '--image={SHIFTER_IMAGE} --entrypoint'
    task_string = '{shifter_setup} {shifter_app} {app_arguments} {filename}'
    if job.setup.execution_type == EXECUTION_TYPES.SHIFTER:
        shifter_setup = shifter_command.format(
            SHIFTER_IMAGE=job.setup.shifter_image if job.setup.shifter_image else _DEFAULT_SHIFTER_IMAGE
        )
        shifter_app = job.run_command
    else:
        shifter_setup = ''
        shifter_app = ''

    app_arguments = " ".join([f"{k} {v if v else ''}" for k, v in job.setup.code_arguments.items()])

    filename = pathlib.Path(job.run_file_name).name

    task_string = task_string.format(shifter_setup=shifter_setup,
                                     shifter_app=shifter_app,
                                     app_arguments=app_arguments,
                                     filename=filename
                                     )

    return task_string

def create_executor_arguments(job: "import rsopt.configuration.schemas.code") -> dict:
    # Really creates Executor.submit() arguments
    if job.use_mpi:
        args = {
            'num_procs': job.setup.cores,
            'num_nodes': None,  # No user interface right now
            'procs_per_node': None, # No user interface right now
            'machinefile': None,  # Add in  setup.machinefile if user wants to control
            'app_args': format_task_string(job),
            'hyperthreads': False,  # Add in  setup.hyperthreads if this is needed
            # 'app_name': None,  # Handled at optimizer setup
            # 'stdout': None,  # Handled at optimizer setup
            # 'stderr': None, # Handled at optimizer setup
            # 'stage_inout': None,  # Not used in rsopt
            # 'dry_run': False, # No support for dry runs in rsopt
            # 'extra_args': None  # Unused (goes to MPI runner)
        }
    else:
        args = {
            'app_args': format_task_string(job)
        }

    # Cannot be overridden
    args['calc_type'] = 'sim'
    args['wait_on_start'] = True

    return args

class EXECUTION_TYPES(str, Enum):
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
