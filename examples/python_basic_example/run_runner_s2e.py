from rsopt.codes.runner.Runner import Runner
import os
import numpy as np

# Dummy objective function
def dummy(H):
    print("H is", H)
    return 0

def get_opal_emittance(H):
    bunch = H['switchyard'].species['Species_0']
    
    enx = np.sqrt(np.average(bunch.x**2) * np.average(bunch.ux**2) - np.average(bunch.x * bunch.ux)**2)
    eny = np.sqrt(np.average(bunch.y**2) * np.average(bunch.uy**2) - np.average(bunch.y * bunch.uy)**2)
    
    H['opal_enx'] = enx
    H['opal_eny'] = eny
    
    return H, 0

# Here we automate the setup of pathing to simulation support files (field maps/parameters/etc.)
# some codes only support absolute pathing requiring this to be set off the location of a user's installation
# This assumes you are working out of fastfelo/examples

# fastfelo_path should be the absolute path to the top level
#  of your fastfelo repository directory
fastfelo_path = 'Set your path here'

# s2e_schema can be obtained from fastfelo/examples/argonne_linac_tessa_s2e
from s2e_schema import schema
with open('s2e_schema.yaml', 'w') as ff:
    ff.write(schema.format(my_path=fastfelo_path))


# Instantiate Runner
runner = Runner('s2e_schema.yaml', objective_function=dummy, 
                processing={'post': {'opal': get_opal_emittance}})

# Parameter inputs are used for the optimizer. This schema file has defaults set for the nominal 
# APS settings for TESSA so we use those for running the simulations
lb, ub, startval = runner.prepare_parameters()

# Start the chain of simulations: OPAL -> elegant -> Genesis
runner.run(startval)