import unittest
import sys
import inspect
from unittest import mock
import numpy as np
import rsopt.libe_tools.simulation_functions.python_simulation_functions as pyfunc
import rsopt.optimizer as opt
radiamodule = mock.MagicMock()
sys.modules["radia"] = radiamodule
from rsopt.codes.radia.sim_functions import hybrid_undulator
from test_configuration import parameters_dict, settings_dict

test_function_signature = inspect.signature(hybrid_undulator)
x_vec = [1, 2, 3, 4, 5]
H = np.array([x_vec], dtype=[('x', float)])
sim_specs = {'out': [('f', float), ('fvec', float, 3)]}


class TestOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = opt.Optimizer()
        self.optimizer.set_parameters(parameters_dict)
        self.optimizer.set_settings(settings_dict)

    def test_class_signature(self):
        pf = pyfunc.PythonFunction(lambda x: x, self.optimizer.parameters, self.optimizer.settings)

        base_signature = settings_dict.copy()
        pyfunc._merge_dicts(parameters_dict, base_signature)

        self.assertEqual(pf.signature.keys(), base_signature.keys())

    def test_x_from_H(self):
        test_x = pyfunc.get_x_from_H(H)
        self.assertTrue(np.all(test_x == x_vec))

    def test_compose_args(self):
        pf = pyfunc.PythonFunction(lambda x: x, self.optimizer.parameters, self.optimizer.settings)
        _, kwargs = pf.compose_args(x_vec, pf.signature)
        for base_key, base_value in zip(parameters_dict.keys(), x_vec):
            self.assertEqual(kwargs[base_key], base_value)

    def test_function_call(self):

        pf = pyfunc.PythonFunction()
