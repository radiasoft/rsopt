from libensemble.sim_funcs import chwirut1
import numpy as np


def eval_chwirut(x1, x2, x3):
    x = [x1, x2, x3]
    f = chwirut1.EvaluateFunction(x)

    func = lambda x: np.sum(np.power(x, 2))
    fsum = func(f)

    return fsum, f


def eval_chwirut_sum(x1, x2, x3):
    x = [x1, x2, x3]
    f = chwirut1.EvaluateFunction(x)

    func = lambda x: np.sum(np.power(x, 2))
    fsum = func(f)

    return fsum


def dummy_obj(*args, **kwargs):
    return (214., np.ones(214))