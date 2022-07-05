import numpy as np


def rosenbrock(x, y, a=0, b=100):
    f = (a - x)**2 + b*(y - x**2)**2
    return f


def rosenbrock_raise(x, y, a=0, b=100):
    assert not np.all(np.isclose([-1.75510204, -0.18367347], [x, y])), "An expected error occurred!"
    f = (a - x)**2 + b*(y - x**2)**2
    return f
