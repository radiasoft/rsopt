import unittest
import numpy as np
import rsopt.optimizer as opt
from rsopt.configuration import jobs


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


class TestOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = opt.Optimizer()
        self.optimizer._config.jobs.append(jobs.Job())

    def test_parameter_array_read(self):
        self.optimizer.set_parameters(parameters_array)

    def test_parameter_dict_read(self):
        self.optimizer.set_parameters(parameters_dict)

    def test_settings_dict_read(self):
        self.optimizer.set_settings(settings_dict)

    def test_set_dimension(self):
        self.optimizer.set_parameters(parameters_dict)
        self.optimizer._set_dimension()

        self.assertEqual(self.optimizer.dimension, len(parameters_dict))
