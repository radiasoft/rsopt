from pymoo.factory import get_problem
import numpy as np


def osy(x1, x2, x3, x4, x5, x6):
    osy_problem = get_problem('osy')
    DIM_OSY = 6
    x_vec = np.array([x1, x2, x3, x4, x5, x6])
    
    d = {}
    osy_problem._evaluate(x_vec.reshape(-1, DIM_OSY), d)
    objectives = d['F'].squeeze()
    constraints = d['G'].squeeze()
    
    # pymoo reverses the sign on the constraints it returns compared to the documented problem
    # https://github.com/anyoptimization/pymoo/blob/c6426a721d95c932ae6dbb610e09b6c1b0e13594/pymoo/problems/multi/osy.py#L28
    # https://pymoo.org/problems/multi/osy.html#OSY
    
    constraints *= -1.0
    
    return objectives, constraints
