import pathlib
import tempfile
import unittest
import rsopt.libe_tools.executors as execs
from pykern import pkyaml
from rsopt import parse

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
        self.assertTrue(pathlib.Path('libe_nodes').is_file())

    def test_detect_rsmpi_resources(self):
        hosts = execs._detect_rsmpi_resources()
        self.assertEqual(2, hosts)

    def test_register_rsmpi_executor_manual(self):
        from libensemble.executors.mpi_executor import MPIExecutor
        hosts = [6, 5]
        controller = execs.register_rsmpi_executor(hosts=hosts)
        self.assertIsInstance(controller, MPIExecutor)
        self.assertTrue(pathlib.Path('libe_nodes').is_file())

    def test_register_rsmpi_executor_auto(self):
        from libensemble.executors.mpi_executor import MPIExecutor
        hosts = 'auto'
        controller = execs.register_rsmpi_executor(hosts=hosts)
        self.assertIsInstance(controller, MPIExecutor)
        self.assertTrue(pathlib.Path('libe_nodes').is_file())

    def tearDown(self):
        self.test_config_file.close()
        try:
            pathlib.Path('libe_nodes').unlink()
        except FileNotFoundError:
            # Not all tests create libe_nodes
            pass

class TestIsParallel(unittest.TestCase):

    def setUp(self) -> None:
        config_file = pathlib.Path('./support/config_six_hump_camel.yaml')
        self.config = pkyaml.load_file(config_file)

    def test_serial_explicit(self):
        _config = self.config.copy()
        _config['codes'][0]['python']['setup']['execution_type'] = 'serial'
        _config = parse.parse_yaml_configuration(_config)

        self.assertFalse(_config.jobs[0].use_mpi)

    def test_serial_one_core_parallel(self):
        _config = self.config.copy()
        _config['codes'][0]['python']['setup']['execution_type'] = 'parallel'
        _config['codes'][0]['python']['setup']['cores'] = 1
        _config = parse.parse_yaml_configuration(_config)

        self.assertTrue(_config.jobs[0].use_mpi)

    def test_serial_one_core_rsmpi(self):
        _config = self.config.copy()
        _config['codes'][0]['python']['setup']['execution_type'] = 'rsmpi'
        _config['codes'][0]['python']['setup']['cores'] = 1
        _config = parse.parse_yaml_configuration(_config)

        self.assertTrue(_config.jobs[0].use_mpi)

    def test_parallel(self):
        _config = self.config.copy()
        _config['codes'][0]['python']['setup']['execution_type'] = 'parallel'
        _config['codes'][0]['python']['setup']['cores'] = 2
        _config = parse.parse_yaml_configuration(_config)

        self.assertTrue(_config.jobs[0].use_mpi)

    def test_rsmpi(self):
        _config = self.config.copy()
        _config['codes'][0]['python']['setup']['execution_type'] = 'rsmpi'
        _config['codes'][0]['python']['setup']['cores'] = 2
        _config = parse.parse_yaml_configuration(_config)

        self.assertTrue(_config.jobs[0].is_parallel)

    def test_force_executor_parallel(self):
        _config = self.config.copy()
        _config['codes'][0]['python']['setup']['execution_type'] = 'parallel'
        _config['codes'][0]['python']['setup']['cores'] = 1
        _config['codes'][0]['python']['setup']['force_executor'] = True
        _config = parse.parse_yaml_configuration(_config)

        self.assertTrue(_config.jobs[0].use_mpi)

    def test_force_executor_series(self):
        _config = self.config.copy()
        _config['codes'][0]['python']['setup']['execution_type'] = 'serial'
        _config['codes'][0]['python']['setup']['cores'] = 1
        _config['codes'][0]['python']['setup']['force_executor'] = True
        _config = parse.parse_yaml_configuration(_config)

        self.assertTrue(_config.jobs[0].use_executor)

    def test_force_executor_rsmpi(self):
        _config = self.config.copy()
        _config['codes'][0]['python']['setup']['execution_type'] = 'rsmpi'
        _config['codes'][0]['python']['setup']['cores'] = 1
        _config['codes'][0]['python']['setup']['force_executor'] = True
        _config = parse.parse_yaml_configuration(_config)

        self.assertTrue(_config.jobs[0].use_executor)





