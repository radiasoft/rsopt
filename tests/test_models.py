import tempfile
import unittest
from rsopt.configuration.setup.elegant import Elegant
from rsopt.configuration.setup.opal import Opal

_TMP_DIR = 'tmp'

# TODO: New set of tests
#  Test case (mixed, caps, lower)
#  bad commands are rejected
#  bad command fields are regjected
#  bad elements are rejected
#  bad element parameters are rejected
#  Test bunched_beam.Po since it is case sensitive?

class TestElegantModels(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def test_one(self):
        Elegant.parse_input_file('support/linac_files/first.ele', shifter=False)


    def test_elegant_case_passing(self):
        # Various mixtures of cases that should be valid
        # Element Names and Parameters can be entered with any combination of case
        # Command values are case-sensitive
        setup = Elegant()
        setup.setup['input_file'] = 'e.ele'
        setup.input_file_model = Elegant.parse_input_file('support/linac_files/first.ele', shifter=False)

        kwarg_dict = {
            'run_setup.default_order': 3,
            'load_parameters.1.allow_missing_parameters': 0,
            'bunched_beam.Po': 600.,  # Correct case for case-sensitive name
            'TUBe.X_mAX': 42,  # Element names and parameters are never case sensitive for rsopt
            'correction_matrix_output.BnL_Units': 1  # Incorrect case for case-sensitive name (is BnL_units)

        }

        new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)
        new_model.write_files(self.test_dir.name)

    def test_elegant_command_name_failure(self):
        # Command not in .ele should not be found
        setup = Elegant()
        setup.setup['input_file'] = 'e.ele'
        setup.input_file_model = Elegant.parse_input_file('support/linac_files/first.ele', shifter=False)

        kwarg_dict = {
            'momentum_aperture.x_initial': 5.0,
        }

        # new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)

        self.assertRaisesRegex(ValueError, 'momentum_aperture was not found',
                               setup._edit_input_file_schema, kwarg_dict)

    def elegant_element_name_failure(self):
        setup = Elegant()
        setup.setup['input_file'] = 'e.ele'
        setup.input_file_model = Elegant.parse_input_file('support/linac_files/first.ele', shifter=False)

        kwarg_dict = {
            'bunched_beam.po': 600.,  # Must be 'Po'
        }

        new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)
        new_model.write_files(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()


class TestOpalModels(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_file = 'support/fast_injector/fast_injector_toX107.in'

    def test_parse(self):
        Opal.parse_input_file(self.input_file, shifter=False)


    def test_opal_case_passing(self):
        # Various mixtures of cases that should be valid
        # Element Names and Parameters can be entered with any combination of case
        # Command values are case-sensitive
        setup = Elegant()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Opal.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'distribution.1.nbin': 12,
            # 'load_parameters.1.allow_missing_parameters': 0,
            # 'bunched_beam.Po': 600.,  # Correct case for case-sensitive name
            # 'TUBe.X_mAX': 42,  # Element names and parameters are never case sensitive for rsopt
            # 'correction_matrix_output.BnL_Units': 1  # Incorrect case for case-sensitive name (is BnL_units)

        }

        new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)
        new_model.write_files(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()