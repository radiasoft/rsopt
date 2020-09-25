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
from rsopt.configuration import jobs

test_function_signature = inspect.signature(hybrid_undulator)
x_vec = [1, 2, 3, 4, 5]
H = np.array([x_vec], dtype=[('x', float)])
sim_specs = {'out': [('f', float), ('fvec', float, 4)]}


class DummyJob:
    pass


class TestOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = opt.Optimizer()
        self.optimizer._config.jobs.append(jobs.Job())
        self.optimizer.set_parameters(parameters_dict)
        self.optimizer.set_settings(settings_dict)

    def test_class_signature(self):
        dummy_job = DummyJob()
        dummy_job.execute = None
        pf = pyfunc.PythonFunction(dummy_job, self.optimizer._config.parameters(job=0),
                                   self.optimizer._config.settings(job=0))

        base_signature = settings_dict.copy()
        pyfunc._merge_dicts(parameters_dict, base_signature)

        self.assertEqual(pf.signature.keys(), base_signature.keys())

    def test_x_from_H(self):
        test_x = pyfunc.get_x_from_H(H)
        self.assertTrue(np.all(test_x == x_vec))

    def test_compose_args(self):
        dummy_job = DummyJob()
        dummy_job.execute = None
        pf = pyfunc.PythonFunction(dummy_job, self.optimizer._config.parameters(job=0),
                                   self.optimizer._config.settings(job=0))
        _, kwargs = pf.compose_args(x_vec, pf.signature)
        for base_key, base_value in zip(parameters_dict.keys(), x_vec):
            self.assertEqual(kwargs[base_key], base_value)

    def test_function_call_function(self):
        objective = mock.MagicMock(name='hybrid_undulator',
                                   return_value=lambda *args, **kwargs: (args, kwargs))
        dummy_job = DummyJob()
        dummy_job.execute = objective()

        pf = pyfunc.PythonFunction(dummy_job, self.optimizer._config.parameters(job=0),
                                   self.optimizer._config.settings(job=0))
        kwargs = {key: i for i, key in enumerate(self.optimizer._config.get_parameters_list('get_parameter_names'))}
        pyfunc._merge_dicts(settings_dict, kwargs, depth=1)

        _, f = pf.call_function(kwargs)

        self.assertEqual(f.keys(), kwargs.keys())

    def test_format_evaluation(self):
        dummy_job = DummyJob()
        dummy_job.execute = None
        pf = pyfunc.PythonFunction(dummy_job, self.optimizer._config.parameters(job=0),
                                   self.optimizer._config.settings(job=0))
        pf.sim_specs = sim_specs
        result = (x_vec[0], x_vec[1:])
        f = pf.format_evaluation(result)

        self.assertEqual(f['f'][0], x_vec[0])
        self.assertTrue(np.all(f['fvec'][0] == x_vec[1:]))

