import unittest
import tempfile
import os
import rsopt.libe_tools.executors as execs

_SSH_CONFIG = \
    """
    Host 5.5.5.5 server.server.server
        Port 4242
        IdentityFile /home/vagrant/jupyter/.rsmpi/host1
    Host 5.5.5.5 server.server.server
        Port 424242
        IdentityFile /home/vagrant/jupyter/.rsmpi/host2
    """


class TestExecutorrsmpi(unittest.TestCase):

    def setUp(self):
        self.test_config_file = tempfile.NamedTemporaryFile()
        execs._RSMPI_CONFIG_PATH = self.test_config_file.name
        self.test_config_file.write(_SSH_CONFIG.encode())
        self.test_config_file.flush()

    def test_generate_rsmpi_node_file(self):
        execs._generate_rsmpi_node_file(4)
        self.assertTrue(os.path.isfile('libe_nodes'))

    def test_detect_rsmpi_resources(self):
        hosts = execs._detect_rsmpi_resources()
        self.assertEqual(2, hosts)

    def test_register_rsmpi_executor_manual(self):
        from libensemble.executors.mpi_executor import MPIExecutor
        hosts = 5
        controller = execs.register_rsmpi_executor(hosts=hosts)
        self.assertIsInstance(controller, MPIExecutor)
        self.assertTrue(os.path.isfile('libe_nodes'))

    def test_register_rsmpi_executor_auto(self):
        from libensemble.executors.mpi_executor import MPIExecutor
        hosts = 'auto'
        controller = execs.register_rsmpi_executor(hosts=hosts)
        self.assertIsInstance(controller, MPIExecutor)
        self.assertTrue(os.path.isfile('libe_nodes'))

    def tearDown(self):
        self.test_config_file.close()
        try:
            os.remove('libe_nodes')
        except OSError:
            pass
