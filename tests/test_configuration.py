import unittest
import numpy as np
import rsopt.configuration as config


parameters_array = np.array([('period', 30., 60., 46.),
                             ('lpy', 1., 10., 5.),
                             ('lmz', 10., 40., 20.),
                             ('lpz', 30., 60., 25.),
                             ('offset', 0.25, 4., 1.)],
                             dtype=[('name', 'U20'), ('min', 'float'), ('max', 'float'), ('start', 'float')])

parameters_dict = {
    'period': {'min': 30., 'max': 60., 'start': 46.},
    'lpy': {'min': 1., 'max': 10., 'start': 5.},
    'lmz': {'min': 10., 'max': 40., 'start': 20.},
    'lpz': {'min': 30., 'max': 60., 'start': 25.},
    'offset': {'min': .25, 'max': 4., 'start': 1.}
}

parameter_test_baseline = {'keys': ['period', 'lpy', 'lmz', 'lpz', 'offset'],
                           'values': [
                               [30., 60., 46.],
                               [1., 10., 5.],
                               [10., 40., 20.],
                               [30., 60., 25.],
                               [0.25, 4., 1.]
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


class TestParameterReaders(unittest.TestCase):

    def test_parameter_array_read(self):
        for reader, base_key, base_value in zip(config.read_parameter_array(parameters_array),
                                                parameter_test_baseline['keys'], parameter_test_baseline['values']):

            self.assertEqual(reader[0], base_key)
            self.assertEqual(list(reader[1]), base_value)

    def test_parameter_dict_read(self):
        for reader, base_key, base_value in zip(config.read_parameter_dict(parameters_dict),
                                                parameter_test_baseline['keys'], parameter_test_baseline['values']):

            self.assertEqual(reader[0], base_key)
            self.assertEqual(list(reader[1]), base_value)


class TestSettingReaders(unittest.TestCase):

    def test_setting_dict_read(self):
        for key, value in config.read_setting_dict(settings_dict):
            print(key, value)
