import unittest
import tempfile
import os

from ruamel.yaml import YAML

from rsopt import _EXAMPLE_REGISTRY
from rsopt.configuration import setup
from rsopt.util import run_path_as_module
#from pykern import pkrunpy

# Load YAML
SUPPORT_PATH = './support/'
yaml = YAML(typ="safe")
with open(_EXAMPLE_REGISTRY, 'r') as rf:
    _EXAMPLES = yaml.load(rf)['examples']

# TODO: Need tests for:
# opal
# elegant
# genesis
# user


class TestInputFileCreation(unittest.TestCase):

    def setUp(self):
        self.run_dir = tempfile.TemporaryDirectory()

    def test_serial_python(self):
        s = setup.Python()
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        self.assertFalse(os.path.isfile(os.path.join(self.run_dir.name, setup._PARALLEL_PYTHON_RUN_FILE)))

    def test_parallel_python(self):
        s = setup.Python()
        s.setup['execution_type'] = 'parallel'
        s.setup['input_file'] = 'test.py'
        s.setup['function'] = 'foo'
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        self.assertTrue(os.path.isfile(os.path.join(self.run_dir.name, setup._PARALLEL_PYTHON_RUN_FILE)))

    def test_rsmpi_python(self):
        s = setup.Python()
        s.setup['execution_type'] = 'rsmpi'
        s.setup['input_file'] = 'test.py'
        s.setup['function'] = 'foo'
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        self.assertTrue(os.path.isfile(os.path.join(self.run_dir.name, setup._PARALLEL_PYTHON_RUN_FILE)))

    def test_force_executor_python(self):
        # Will not work until is_parallel refactored into setup class
        s = setup.Python()
        s.setup['execution_type'] = 'serial'
        s.setup['force_executor'] = True
        s.setup['input_file'] = 'test.py'
        s.setup['function'] = 'foo'
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        self.assertTrue(os.path.isfile(os.path.join(self.run_dir.name, setup._PARALLEL_PYTHON_RUN_FILE)))

    def tearDown(self):
        self.run_dir.cleanup()


class TestPythonRunFile(unittest.TestCase):

    def setUp(self):
        self.run_dir = tempfile.TemporaryDirectory()
        # Worker process normally will be in the run_dir, but that isn't true in the test
        self.input_file = os.path.join(self.run_dir.name, 'test.py')
        with open(self.input_file, 'w') as ff:
            ff.write('def foo(*args, **kwargs):\n\treturn 0')

    def test_argument_dict(self):
        s = setup.Python()
        s.setup['execution_type'] = 'parallel'
        s.setup['input_file'] = self.input_file
        s.setup['function'] = 'foo'
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        path = os.path.join(self.run_dir.name, setup._PARALLEL_PYTHON_RUN_FILE)
        module = run_path_as_module(path)
        input_dict = getattr(module, 'input_dict')

        for k, v in d.items():
            self.assertIn(k, input_dict.keys())
            self.assertEqual(v, input_dict[k])

    def tearDown(self):
        self.run_dir.cleanup()


