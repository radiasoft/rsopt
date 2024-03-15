import os
import logging

from libensemble.executors.mpi_executor import MPIExecutor
from pykern import pkyaml
from rsopt import EXECUTOR_SCHEMA

EXECUTOR_SCHEMA = pkyaml.load_file(EXECUTOR_SCHEMA)
logger = logging.getLogger(__name__)
# To change logging level for just this module
# logger.setLevel(logging.DEBUG)

_RSMPI_CONFIG_PATH = EXECUTOR_SCHEMA['rsmpi']['config_path']


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
