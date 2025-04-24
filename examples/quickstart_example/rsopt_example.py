def six_hump_camel_func(x, y):
    """
    Definition of the six-hump camel
    """
    x1 = x
    x2 = y
    term1 = (4-2.1*x1**2+(x1**4)/3) * x1**2
    term2 = x1*x2
    term3 = (-4+4*x2**2) * x2**2

    return term1 + term2 + term3
