from rsopt.codes.radia.sim_functions import optimize_objective_km_appleII, optimize_objective_1stint_appleII
from rsopt.libe_tools.optimizer import libEnsembleOptimizer
import numpy as np

####################
# Start configuring a local optimizer run through libEnsemble
####################
optimizer = libEnsembleOptimizer()

####################
# Set functions used for simulation and objective evaluation
# Note: simulation function may also directly return the objective value
####################
# sim_func = optimize_objective_km_appleII # if optimize kickmap, uncomment this line, and line 22-25, 49-55; comment the next line, and line 26-32, 38-41
sim_func = optimize_objective_1stint_appleII #if optimize the 1st field integral, uncomment this line, and line 26-32, 38-41; comment the previous line, and line 22-25, 49-55
optimizer.set_simulation(sim_func)

####################
# Set optimizer parameters
####################
parameters = np.array([
                    #    ('lx', 15., 50., 34.),
                    #    ('lz', 15., 50., 34.),
                    #    ('cx', 1., 10., 5.),
                    #    ('cz', 1., 10., 5.)
                       ('bs1_fac', 0.06,0.15, 0.0776),
                       ('bs2_fac', 0.12, 0.13, 0.1242),
                       ('bs3_fac', 0., 0.2, 0.1473),
                       ('s1_fac', 0., 0.1, 0.0203),
                       ('s2_fac', 0., 0.15, 0.0915),
                       ('s3_fac', 0., 1., 0.0203),
                       ('bs2dz', 0, 1., 0.16961)
                      ],
                       dtype=[('name', 'U20'), ('min', 'float'), ('max', 'float'), ('start', 'float')])

optimizer.set_parameters(parameters)
settings = {
    'lx': 34., #Horizontal Magnet Size
    'lz': 34., #Vertical Magnet Size
    'cx': 5., #Horizontal Notch size
    'cz': 5., #Vertical Notch size
    'gap': 11.5,                 # Magnetic Gap in[mm]
    'gapx': 1.,                 # Horizontal gap between magnet arrays in [mm]
    'air': 0.05, #Air Space between Magnets in Longitudinal Direction
    'phase': 0., #0.2923*per #0.29*per #0.28*per #per/2. #per/4. #Longitudinal Shift between Magnet Arrays
    'phaseType': 1, #=1 means Parallel, -1 Anti-Parallel displacement of Magnet Arrays
    'period':50.,                 # Undulator Period in [mm] 
    'period_number': 40,                #Number of Periods (should be EVEN here to make correct integer (M3+M5) modular structure!)
    # 'bs1_fac':3.82/49.2,
    # 'bs2_fac':6.11/49.2,
    # 'bs3_fac':7.25/49.2,
    # 's1_fac':1./49.2,
    # 's2_fac':4.5/49.2,
    # 's3_fac':1./49.2,
    # 'bs2dz': 0., #(*0.16961;*) #Vertical displacement of vertically-magnetised termination block
    #Material Constants
    'br': 1.27, #Remanent Magnetization
    'mu': [0.05,0.15], #[0.06,0.17] #Suscettivita
    #Subdivision Params
    'nDiv': [3,2,3], 
    #Quasi-Periodic Perturbation
    'indsMagDispQP': [-77, -63, -49, -35, -21, -7, 7, 21, 35, 49, 63, 77], #None #Indexes of magnets counting from the central magnet of the structure, which has index 0.
    'vertMagDispQP': 0., 
}

optimizer.set_settings(settings)

####################
# setup optimizer
####################
optimizer_settings = { 'xtol_rel': 1e-6, #1e-4
                      'ftol_rel': 1e-6
                      }#'gen_batch_size': 2
optimizer.set_optimizer(software='nlopt',
                        method='LN_BOBYQA',  # Optimization algorithm
                        options=optimizer_settings)

####################
# run optimization
####################
optimizer.set_exit_criteria({'sim_max': 500})
H, _, _ = optimizer.run()
np.save('undulator_optimizer_history_km.npy', H)
