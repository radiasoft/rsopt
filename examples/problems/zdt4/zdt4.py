from pymoo.problems import get_problem
import numpy as np


def obj_zdt4(x):
    zdt4 = get_problem('zdt4')

    return zdt4.evaluate(np.array(x))


def obj_zdt4_kwargs(x0, x1, x2, x3, x4, x5, x6, x7, x8, x9):
    x = [x0, x1, x2, x3, x4, x5, x6, x7, x8, x9]
    zdt4 = get_problem('zdt4')

    return zdt4.evaluate(np.array(x))
