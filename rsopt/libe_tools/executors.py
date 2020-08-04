from libensemble.executors import MPIExecutor
import os

_CONFIG_PATH = '/home/vagrant/jupyter/.rsmpi/ssh_config'


def register_rsmpi_executor(sim_app, hosts='auto', cores_on_node=None):
    """
    Create an MPIExecutor that can use rsmpi
    :param sim_app: (str) Name of application to be executed
    :param hosts: (str or int) If 'auto' then all rsmpi resources are detected and used. Otherwise specify number
                               of hosts as an int.
    :param cores_on_node: (tuple) Defaults to (16, 16). Number of physical cores and logical cores on the hosts.
    :return: libensemble.executors.mpi_executor.MPIExecutor object
    """

    try:
        hosts = int(hosts)
    except TypeError:
        hosts = _detect_rsmpi_resources()

    _generate_rsmpi_node_file(hosts)

    cores_on_node = (16, 16) if not cores_on_node else cores_on_node
    customizer = {'mpi_runner': 'mpich',
                  'runner_name': 'libensemble-rsmpi',
                  'cores_on_node': cores_on_node,
                  'node_file': 'libe_nodes'}
    jobctrl = MPIExecutor(custom_info=customizer)
    jobctrl.register_calc(full_path=sim_app, calc_type='sim')

    return jobctrl


def _detect_rsmpi_resources():
    hosts = 0
    assert os.path.isfile(_CONFIG_PATH), "rsmpi configuration does not exist"
    with open(_CONFIG_PATH, 'r') as ff:
        for line in ff.readlines():
            if 'Host' in line:
                hosts += 1

    assert hosts > 0, 'No hosts listed in rsmpi configuration'

    return hosts


def _generate_rsmpi_node_file(nodes):
    with open('libe_nodes', 'w') as ff:
        for node in range(nodes):
            ff.write(str(node))
