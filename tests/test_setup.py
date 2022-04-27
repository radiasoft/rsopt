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
HOME = os.getcwd()

# I am doing something wrong with the tempdir run
# Tests all pass when run individually but if the whole test is executed then test_executor_timeout fails

class TestSetupFeatures(unittest.TestCase):
    # For these tests the process moves to SUPPORT_PATH before starting the test
    def setUp(self):
        self.run_dir = tempfile.TemporaryDirectory()
        self.timeout_config = os.path.join('config_timeout.yaml')
        self.ignored_files_config = os.path.join('config_ignored_files.yaml')
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

    def test_ignored_files(self):
        # parsing assumes you are same directory as config file
        os.chdir(SUPPORT_PATH)

        config_yaml = parse.read_configuration_file(self.ignored_files_config)
        _config = parse.parse_yaml_configuration(config_yaml)

    def test_ignored_files_exception(self):
        # parsing assumes you are same directory as config file
        os.chdir(SUPPORT_PATH)

        config_yaml = parse.read_configuration_file(self.ignored_files_config)
        # Take out first ignored_files declaration
        config_yaml.codes[0].elegant.setup.ignored_files = []

        self.assertRaisesRegex(AssertionError, 'file=transverse_w_type1.sdds missing',
                               parse.parse_yaml_configuration, config_yaml)

    def tearDown(self):
        os.chdir(HOME)
        self.run_dir.cleanup()
