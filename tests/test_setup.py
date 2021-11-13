import unittest
import tempfile
from rsopt import parse
from rsopt import run
from rsopt.libe_tools import tools
import os
import shutil


SUPPORT_PATH = './support/'
TIMEOUT_STATUS_MESSAGE = 'Worker killed task on Timeout'
COMPLETED_STATUS_MESSAGE = 'Completed'


class TestSetupFeatures(unittest.TestCase):
    # For these tests the process moves to SUPPORT_PATH before starting the test
    def setUp(self):
        self.run_dir = tempfile.TemporaryDirectory()
        self.timeout_config = os.path.join('config_timeout.yaml')
        shutil.copy(os.path.join(SUPPORT_PATH, self.timeout_config), self.run_dir.name)
        shutil.copy(os.path.join(SUPPORT_PATH, 'six_hump_camel.py'), self.run_dir.name)

    def test_executor_timeout(self):
        os.chdir(self.run_dir.name)
        config_yaml = parse.read_configuration_file(self.timeout_config)
        config_yaml['codes'][0]['python']['settings']['t'] = 5.0
        config_yaml['codes'][0]['python']['setup']['timeout'] = 1.0
        _config = parse.parse_yaml_configuration(config_yaml)
        software = _config.options.NAME
        runner = run.run_modes[software](_config)
        H, persis_info, _ = runner.run()

        frame = tools.parse_stat_file('libE_stats.txt')
        frame.to_csv('resr.csv')
        for row in frame.status[:2]:
            self.assertEqual(row, TIMEOUT_STATUS_MESSAGE)

    def test_executor_complete_with_timeout(self):
        os.chdir(self.run_dir.name)
        config_yaml = parse.read_configuration_file(self.timeout_config)
        config_yaml['codes'][0]['python']['settings']['t'] = 1.0
        config_yaml['codes'][0]['python']['setup']['timeout'] = 5.0
        _config = parse.parse_yaml_configuration(config_yaml)
        software = _config.options.NAME
        runner = run.run_modes[software](_config)
        H, persis_info, _ = runner.run()

        frame = tools.parse_stat_file('libE_stats.txt')
        for row in frame.status[:2]:
            self.assertEqual(row, COMPLETED_STATUS_MESSAGE)

    def test_force_executor(self):
        from libensemble.executors.mpi_executor import MPIExecutor
        os.chdir(self.run_dir.name)
        config_yaml = parse.read_configuration_file(self.timeout_config)
        _config = parse.parse_yaml_configuration(config_yaml)
        software = _config.options.NAME
        runner = run.run_modes[software](_config)
        runner._configure_executors()
        self.assertTrue(isinstance(runner.executor, MPIExecutor))
        self.assertTrue(runner._config.jobs[0].executor)

    def tearDown(self):
        self.run_dir.cleanup()
