import numpy as np


def tnk(x1, x2):
    objectives = (x1, x2)
    constraints = (x1 ** 2 + x2 ** 2 - 1.0 - 0.1 * np.cos(16 * np.arctan2(x1, x2)),
                   (x1 - 0.5) ** 2 + (x2 - 0.5) ** 2)

    return objectives, constraints