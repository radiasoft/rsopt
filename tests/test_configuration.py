import unittest
import numpy as np
import rsopt.configuration as config
from rsopt.configuration.options import options
from rsopt.parse import read_configuration_file, parse_yaml_configuration
SUPPORT_PATH = './support/'

parameters_array = np.array([('period', 30., 60., 46.),
                             ('lpy', 1., 10., 5.),
                             ('lmz', 10., 40., 20.),
                             ('lpz', 30., 60., 35.),
                             ('offset', 0.25, 4., 1.)],
                             dtype=[('name', 'U20'), ('min', 'float'), ('max', 'float'), ('start', 'float')])

parameters_dict = {
    'period': {'min': 30., 'max': 60., 'start': 46.},
    'lpy': {'min': 1., 'max': 10., 'start': 5.},
    'lmz': {'min': 10., 'max': 40., 'start': 20.},
    'lpz': {'min': 30., 'max': 60., 'start': 35.},
    'offset': {'min': .25, 'max': 4., 'start': 1.}
}

parameter_test_baseline = {'keys': ['period', 'lpy', 'lmz', 'lpz', 'offset'],
                           'values': [
                               [30., 60., 46., None],
                               [1., 10., 5., None],
                               [10., 40., 20., None],
                               [30., 60., 35., None],
                               [0.25, 4., 1., None]
                            ]
                           }

settings_dict = {
    'lpx': 65,
    'pole_properties': 'h5',
    'pole_segmentation': [2, 2, 5],
    'pole_color': [1, 0, 1],
    'lmx': 65,
    'magnet_properties': 'sdds',
    'magnet_segmentation': [1, 3, 1],
    'magnet_color': [0, 1, 1],
    'gap': 20.
}

options_dict = {'software': 'nlopt',
                 'software_options': {'xtol_abs': '1e-6',
                 'ftol_abs': '1e-6',
                 'record_interval': 2},
                 'method': 'LN_SBPLX',
                 'exit_criteria': {'sim_max': 10000, 'wall_clock': '1e4'},
                 'objective_function': []
                }


class TestParameterReaders(unittest.TestCase):

    def test_parameter_array_read(self):
        for reader, base_key, base_value in zip(config.parameters.read_parameter_array(parameters_array),
                                                parameter_test_baseline['keys'], parameter_test_baseline['values']):

            self.assertEqual(reader[0], base_key)
            self.assertEqual(list(reader[1]), base_value)

    def test_parameter_dict_read(self):
        for reader, base_key, base_value in zip(config.parameters.read_parameter_dict(parameters_dict),
                                                parameter_test_baseline['keys'], parameter_test_baseline['values']):

            self.assertEqual(reader[0], base_key)
            self.assertEqual(list(reader[1]), base_value)


class TestSettingReaders(unittest.TestCase):

    def test_setting_dict_read(self):
        for key, value in config.settings.read_setting_dict(settings_dict):
            print(key, value)


class TestOptionsReaders(unittest.TestCase):
    # Should not rely on hardcoded values
    software_key = 'software'
    required_keys = {'nlopt': {'method': 'LN_SBPLX',
                               'exit_criteria': 'fill'},
                     'aposmm': {'method': 'LN_COBYLA',
                                'exit_criteria': 'fill',
                                 'initial_sample_size': 42},
                     'pysot': {'exit_criteria': 'fill'},
                     'dlib': {'exit_criteria': 'fill'},
                     'mesh_scan': {},
                     'nsga2': {'n_objectives': 2,
                               'exit_criteria': 'fill'},
                     'dfols': {'components': 128,
                               'exit_criteria': 'fill'},
                     'scipy': {'method': 'Nelder-Mead',
                               'exit_criteria': 'fill'},
                     'lh_scan': {'batch_size': 512},
                     'mobo': {'constraints': 80, 'objectives': 42, 'reference': [2000, 2000], 'exit_criteria': 'fill'}}

    def test_options_set(self):
        for option_name, option_class in options.option_classes.items():
            opt_dict = self.required_keys[option_name]
            opt_dict[self.software_key] = option_name
            option_obj = config.options.Options.get_option(opt_dict)()
            self.assertIsInstance(option_obj, option_class)

    def test_missing_req_options(self):

        for option_name, option_class in options.option_classes.items():
            if option_class.REQUIRED_OPTIONS:
                opt_dict = {}
                opt_dict[self.software_key] = option_name
                with self.assertRaises(AssertionError):  # could use assertRaisesRegex and loop from pulling keys
                    option_obj = config.options.Options.get_option(opt_dict)()


class TestConfigurationSetup(unittest.TestCase):

    def test_option_read(self):
        cfg = config.configuration.Configuration()
        cfg.options = options_dict


class TestYAMLtoConfiguration(unittest.TestCase):
    config_file = SUPPORT_PATH + 'config_six_hump_camel.yaml'

    def test_config_read(self):
        config_file = read_configuration_file(self.config_file)

    def test_config_import(self):
        config_file = read_configuration_file(self.config_file)
        parse_yaml_configuration(config_file, configuration=None)

    def test_job_setup(self):
        config_file = read_configuration_file(self.config_file)
        config = parse_yaml_configuration(config_file, configuration=None)

        python_job = config.jobs[0]
        setup = python_job._setup

        setup.setup['input_file'] = setup.setup['input_file']

        assert callable(setup.function)




