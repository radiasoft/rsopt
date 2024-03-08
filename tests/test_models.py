import tempfile
import unittest
from rsopt.configuration.setup.elegant import Elegant
from rsopt.configuration.setup.opal import Opal
from rsopt.configuration.setup.madx import Madx
from rsopt.configuration.setup.genesis import Genesis

_TMP_DIR = 'tmp'

# NOTE: Would be a good candidate to re-write in pytest to leverage parametrize

#  bad commands are rejected
#  bad command fields are regjected
#  bad elements are rejected
#  bad element parameters are rejected


class TestElegantModels(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def test_one(self):
        Elegant.parse_input_file('support/linac_files/first.ele', shifter=False)


    def test_elegant_case_passing(self):
        # Various mixtures of cases that should be valid
        # Element Names and Parameters can be entered with any combination of case
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

    def test_elegant_element_name_failure(self):
        setup = Elegant()
        setup.setup['input_file'] = 'e.ele'
        setup.input_file_model = Elegant.parse_input_file('support/linac_files/first.ele', shifter=False)

        kwarg_dict = {
            'not_an_element.k1': 600.,  # Must be 'Po'
        }

        self.assertRaisesRegex(ValueError, 'not_an_element was not found',
                               setup._edit_input_file_schema, kwarg_dict)

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
        setup = Opal()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Opal.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'distribution.1.nbin': 12,
            'FIELDSOLVER.parFFTx': 'true',
            'Q_107.K1S': 50.,  # Correct case for case-sensitive name
            'cc2.fReq': 1e9,  # Correct case for case-sensitive name
        }

        new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)
        new_model.write_files(self.test_dir.name)

    def test_opal_command_name_failure(self):
        # Command not in .in, should not be found
        setup = Opal()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Opal.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'geometry.length': 5.0,
        }

        # new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)

        self.assertRaisesRegex(ValueError, 'geometry was not found',
                               setup._edit_input_file_schema, kwarg_dict)

    def test_opal_element_name_failure(self):
        setup = Opal()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Opal.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'not_an_element.k1': 600.,
        }

        self.assertRaisesRegex(ValueError, 'not_an_element was not found',
                               setup._edit_input_file_schema, kwarg_dict)

    def test_opal_element_parameter_failure(self):
        setup = Opal()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Opal.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'gun.k1': 600.,
        }

        self.assertRaisesRegex(NameError, 'Parameter: k1 is not found',
                               setup._edit_input_file_schema, kwarg_dict)

    def tearDown(self):
        self.test_dir.cleanup()


class TestMadxModels(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_file = 'support/atr/ATR-U-and-W-lines.madx'

    def test_parse(self):
        Madx.parse_input_file(self.input_file, shifter=False)


    def test_madx_case_passing(self):
        # Various mixtures of cases that should be valid
        # Element Names and Parameters can be entered with any combination of case
        # Command values are case-sensitive
        setup = Madx()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Madx.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'ptc_twiss.betx': 12.0,
            'ptc_observe.25.place': 'Marker300',
            'pTc_oBSErve.166.PLACE': 'Marker302',
            'UQ10.k1': 50.,  # Correct case for case-sensitive name
            'wd6.AnGlE': 0.2341,  # Correct case for case-sensitive name
        }

        new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)
        new_model.write_files(self.test_dir.name)

    def test_madx_command_name_failure(self):
        # Command not in .in, should not be found
        setup = Madx()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Madx.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'ptc_track_line.turns': 5,
        }

        self.assertRaisesRegex(ValueError, 'ptc_track_line was not found',
                               setup._edit_input_file_schema, kwarg_dict)

    def test_madx_element_name_failure(self):
        setup = Madx()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Madx.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'not_an_element.k1': 600.,
        }

        self.assertRaisesRegex(ValueError, 'not_an_element was not found',
                               setup._edit_input_file_schema, kwarg_dict)

    def test_madx_element_parameter_failure(self):
        setup = Madx()
        setup.setup['input_file'] = 'e.in'
        setup.input_file_model = Madx.parse_input_file(self.input_file, shifter=False)

        kwarg_dict = {
            'wd6.fake_parameter': 600.,
        }

        self.assertRaisesRegex(NameError, 'Parameter: fake_parameter is not found',
                               setup._edit_input_file_schema, kwarg_dict)

    def tearDown(self):
        self.test_dir.cleanup()


class TestGenesisModels(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_file_pegasus = 'support/genesis/genesis_pegasus.in'
        self.input_file_tessa = 'support/genesis/genesis_tessa.in'

    def test_parse_no_lattice(self):
        Genesis.parse_input_file(self.input_file_pegasus, shifter=False)

    def test_parse_with_lattice(self):
        # lume-genesis expects lattice to be local directory, does not check input file name for a directory path
        Genesis.parse_input_file(self.input_file_tessa, shifter=False)

    def test_genesis_parameter_edit(self):
        setup = Genesis()
        setup.setup['input_file'] = 'not_used'
        setup.input_file_model = Genesis.parse_input_file(self.input_file_tessa, shifter=False)

        kwarg_dict = {
            'CURPEAK': 155.0,
            'DElGAm': 0.04,
            'NSCZ': 0
        }

        new_model = setup._edit_input_file_schema(kwarg_dict=kwarg_dict)
        new_model.configure_genesis(workdir=self.test_dir.name)

        new_model.write_input_file()
        new_model.write_beam()
        new_model.write_lattice()

    def test_genesis_bad_parameter(self):
        setup = Genesis()
        setup.setup['input_file'] = 'not_used'
        setup.input_file_model = Genesis.parse_input_file(self.input_file_pegasus, shifter=False)

        kwarg_dict = {
            'NOTAPAR': 155.0,
        }

        self.assertRaisesRegex(ValueError, '`notapar` was not found',
                               setup._edit_input_file_schema, kwarg_dict)
