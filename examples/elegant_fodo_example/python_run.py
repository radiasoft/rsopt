from rsopt.libe_tools.optimizer import libEnsembleOptimizer
import numpy as np
# Optimization may be built from setup of a Python script or by specifying a YAML configuration file
#   that describes the optimization. Shown here is the Python setup local six hump camel optimization
#   the corresponding YAML configured execution can be found in run__six_hump_camel_from_yaml.sh

# Start configuring a local optimizer run through libEnsemble
optimizer = libEnsembleOptimizer()

# Set functions used for simulation and objective evaluation
# Note: simulation function directly returns the objective value in this example

optimizer.add_simulation('fodo_opt.ele', 'elegant')

# Set optimizer parameters
parameters = np.array([('Q1.K1', -15., 15.,  5.),
                       ('Q2.K1', -15., 15., -5.)],
                       dtype=[('name', 'U20'), ('min', 'float'), ('max', 'float'), ('start', 'float')])

optimizer.set_parameters(parameters)


# setup optimizer
optimizer_settings = {'xtol_abs': 1e-8,
                      'ftol_abs': 1e-8,
                      'record_interval': 2}

optimizer.set_optimizer(software='nlopt',
                        method='LN_BOBYQA',
                        objective_function= ['obj_fodo_opt.py', 'obj_f'],
                        options=optimizer_settings)

# run optimization
optimizer.set_exit_criteria({'sim_max': 30})
# If `clean_work_dir` is  True the optimizer will not run if working_directory exists and is not empty
#
H, _, _ = optimizer.run(clean_work_dir=True)

print(H)


def test_optimizer_result():
    print('result', H['x'][-1])
    return 0
