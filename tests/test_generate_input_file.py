import unittest
import tempfile
import os

import rsopt.configuration.setup.python
from rsopt import EXAMPLE_REGISTRY
from rsopt.configuration import setup
from pykern import pkyaml
from pykern import pkrunpy
SUPPORT_PATH = './support/'
_EXAMPLES = pkyaml.load_file(EXAMPLE_REGISTRY)['examples']

# TODO: Need tests for:
# opal
# elegant
# genesis
# user


class TestInputFileCreation(unittest.TestCase):

    def setUp(self):
        self.run_dir = tempfile.TemporaryDirectory()

    def test_serial_python(self):
        s = rsopt.configuration.setup.python.Python()
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        self.assertFalse(os.path.isfile(os.path.join(self.run_dir.name,
                                                     rsopt.configuration.setup.python._PARALLEL_PYTHON_RUN_FILE)))

    def test_parallel_python(self):
        s = rsopt.configuration.setup.python.Python()
        s.setup['execution_type'] = 'parallel'
        s.setup['input_file'] = 'test.py'
        s.setup['function'] = 'foo'
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        self.assertTrue(os.path.isfile(os.path.join(self.run_dir.name,
                                                    rsopt.configuration.setup.python._PARALLEL_PYTHON_RUN_FILE)))

    def test_rsmpi_python(self):
        s = rsopt.configuration.setup.python.Python()
        s.setup['execution_type'] = 'rsmpi'
        s.setup['input_file'] = 'test.py'
        s.setup['function'] = 'foo'
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        self.assertTrue(os.path.isfile(os.path.join(self.run_dir.name,
                                                    rsopt.configuration.setup.python._PARALLEL_PYTHON_RUN_FILE)))

    def test_force_executor_python(self):
        # Will not work until is_parallel refactored into setup class
        s = rsopt.configuration.setup.python.Python()
        s.setup['execution_type'] = 'serial'
        s.setup['force_executor'] = True
        s.setup['input_file'] = 'test.py'
        s.setup['function'] = 'foo'
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        self.assertTrue(os.path.isfile(os.path.join(self.run_dir.name,
                                                    rsopt.configuration.setup.python._PARALLEL_PYTHON_RUN_FILE)))

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
        s = rsopt.configuration.setup.python.Python()
        s.setup['execution_type'] = 'parallel'
        s.setup['input_file'] = self.input_file
        s.setup['function'] = 'foo'
        d = {'a': 1,
             'b': 2,
             'c': 'c'}
        s.generate_input_file(d, self.run_dir.name)
        path = os.path.join(self.run_dir.name,
                            rsopt.configuration.setup.python._PARALLEL_PYTHON_RUN_FILE)
        module = pkrunpy.run_path_as_module(path)
        input_dict = getattr(module, 'input_dict')

        for k, v in d.items():
            self.assertIn(k, input_dict.keys())
            self.assertEqual(v, input_dict[k])

    def tearDown(self):
        self.run_dir.cleanup()


