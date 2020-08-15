from rsopt.libe_tools.optimizer import libEnsembleOptimizer
import numpy as np

# Start configuring a local optimizer run through libEnsemble
optimizer = libEnsembleOptimizer()

# Set functions used for simulation and objective evaluation
# Note: simulation function directly returns the objective value in this example
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


optimizer.set_simulation(six_hump_camel_func)

# Set optimizer parameters
parameters = np.array([('x', -3., 3.,  0.08),
                       ('y', -2., 2., -0.7)],
                       dtype=[('name', 'U20'), ('min', 'float'), ('max', 'float'), ('start', 'float')])

optimizer.set_parameters(parameters)


# setup optimizer
optimizer_settings = {'xtol_abs': 1e-6,
                      'ftol_abs': 1e-6}
optimizer.set_optimizer(method='LN_BOBYQA',
                        options=optimizer_settings)

# run optimization
optimizer.set_exit_criteria({'sim_max': 30})
H, _, _ = optimizer.run()

print(H)

assert np.all(np.isclose(H['x'][-1], [0.08979957, -0.71264018], rtol=0., atol=1e-7)), "Min. not found"
