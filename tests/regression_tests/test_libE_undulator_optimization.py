# from rsopt.codes.radia.sim_functions import hybrid_undulator, materials, undulatorK_simple
from rsopt.libe_tools.optimizer import libEnsembleOptimizer
import numpy as np

# Start configuring a local optimizer run through libEnsemble
optimizer = libEnsembleOptimizer()

# Set functions used for simulation and objective evaluation
# Note: simulation function directly returns the objective value in this example


def dummy_obj(*args, **kwargs):
    print('CALLED with:', kwargs)
    sum = kwargs['period'] + kwargs['lpy'] + kwargs['lmz'] + kwargs['lpz'] + kwargs['offset']

    return sum

optimizer.set_simulation(dummy_obj)

# Set optimizer parameters
parameters = np.array([('period', 30., 60., 46.),
                       ('lpy', 1., 10., 5.),
                       ('lmz', 10., 40., 20.),
                       ('lpz', 30., 60., 45.),
                       ('offset', 0.25, 4., 1.)],
                       dtype=[('name', 'U20'), ('min', 'float'), ('max', 'float'), ('start', 'float')])

optimizer.set_parameters(parameters)


# Set optimizer settings
def dummy_materials(array1, array2, str1, float1):
    return np.sum(array1) * float1, np.sum(array2) * float1


ironH = [  0.8,   1.5,     2.2,    3.6,    5.0,     6.8,     9.8,    18.0,
          28.0,   37.5,   42.0,   55.0,   71.5,    80.0,    85.0,    88.0,
          92.0,  100.0,  120.0,  150.0,  200.0,   300.0,   400.0,   600.0,
         800.0, 1000.0, 2000.0, 4000.0, 6000.0, 10000.0, 25000.0, 40000.0]
ironM = [0.000998995, 0.00199812, 0.00299724, 0.00499548, 0.00699372, 0.00999145, 0.0149877, 0.0299774,
         0.0499648,   0.0799529,  0.0999472,  0.199931,   0.49991,    0.799899,   0.999893, 1.09989,
         1.19988,     1.29987,    1.41985,    1.49981,    1.59975,    1.72962,    1.7995,   1.89925,
         1.96899,     1.99874,    2.09749,    2.19497,    2.24246,    2.27743,    2.28958,  2.28973]
mp, mm = dummy_materials(ironH, ironM, 'NdFeB', 1.2)

settings = {
    # FUTURE: Not supporting nested parameters in nested items. The general case would be messy.
    #   would need to iterate down an arbitrary number of levels and be able to replace string instances
    #   with reference to new value
    # 'pole_dimensions': [65, 'pole_tip_length', 'pole_tip_height'],
    'lpx': 65,
    'pole_properties': mp,
    'pole_segmentation': [2, 2, 5],
    'pole_color': [1, 0, 1],
    'lmx': 65,
    # FUTURE: Not supporting lambda functions immediately. Requires inspect as imagined here.
    # 'lmy': lambda period, pole_tip_length: period / 2. - pole_tip_length,
    'magnet_properties': mm,
    'magnet_segmentation': [1, 3, 1],
    'magnet_color': [0, 1, 1],
    'gap': 20.,
    'period_number': 2
}

optimizer.set_settings(settings)

# setup optimizer
optimizer_settings = {'xtol_rel': 1e-4,
                      'gen_batch_size': 2}

optimizer.set_optimizer(software='nlopt',
                        method='LN_BOBYQA',
                        options=optimizer_settings)

# run optimization
optimizer.set_exit_criteria({'sim_max': 1000})
H, _, _ = optimizer.run()


def test_optimizer_result():
    print(H)
    assert np.abs(H['f'][-1] - 71.25) < 1e-12
