from libensemble.executors import MPIExecutor
import os


def register_rsmpi_executor(sim_app, hosts='auto', cores_on_node=None):
    """
    Create an MPIExecutor that can use rsmpi
    :param sim_app: (str) Name of application to be executed
    :param hosts: (str or int) If 'auto' then all rsmpi resources are detected and used. Otherwise specify number
                               of hosts as an int.
    :param cores_on_node: (tuple) Defaults to (16, 16). Number of physical cores and logical cores on the hosts.
    :return: libensemble.executor.MPIExecutor object
    """

    try:
        hosts = int(hosts)
    except ValueError:
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
    config_path = '/home/vagrant/jupyter/.rsmpi/ssh_config'
    assert os.path.isfile(config_path), "rsmpi configuration does not exist"
    with open(config_path, 'r') as ff:
        for line in ff.readlines():
            if 'Host' in line:
                hosts += 1

    assert hosts > 0, 'No hosts listed in rsmpi configuration'

    return hosts


def _generate_rsmpi_node_file(nodes):
    with open('libe_nodes', 'w') as ff:
        for node in range(nodes):
            ff.write(node)
