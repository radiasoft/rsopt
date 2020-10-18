import tempfile
import unittest
from rsopt.configuration.setup import Elegant

_TMP_DIR = 'tmp'

class TestElegantModels(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def test_one(self):
        Elegant.parse_input_file('support/linac_files/first.ele')

    def test_two(self):
        setup = Elegant()
        setup.setup['input_file'] = 'e.ele'
        setup.input_file_model = Elegant.parse_input_file('support/linac_files/first.ele')

        kwarg_dict = {
            'run_setup.default_order': 3,
            'load_parameters.1.allow_missing_parameters': 0
        }

        new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)
        new_model.write_files(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()
