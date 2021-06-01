import subprocess
import numpy as np
from rsbeams.rsdata.SDDS import readSDDS

def obj_f(_):

    analysis_command = ["sddsanalyzebeam", "run_setup.output.sdds", "output.anb"]
    subprocess.call(analysis_command)

    anb = readSDDS("output.anb")
    anb.read()

    betax, betax_target = anb.columns['betax'].squeeze(), 10.
    betay, betay_target = anb.columns['betay'].squeeze(), 10.
    alphax, alphax_target = anb.columns['alphax'].squeeze(), 1.
    alphay, alphay_target = anb.columns['alphay'].squeeze(), 1.

    obj_val = np.sqrt((betax - betax_target)**2 +
                      (betay - betay_target)**2 +
                      (alphax - alphax_target)**2 +
                      (alphay - alphay_target)**2)

    return obj_val

def obj_f_dfols(_):

    analysis_command = ["sddsanalyzebeam", "run_setup.output.sdds", "output.anb"]
    subprocess.call(analysis_command)

    anb = readSDDS("output.anb")
    anb.read()

    betax, betax_target = anb.columns['betax'].squeeze(), 10.
    betay, betay_target = anb.columns['betay'].squeeze(), 10.
    alphax, alphax_target = anb.columns['alphax'].squeeze(), 1.
    alphay, alphay_target = anb.columns['alphay'].squeeze(), 1.

    obj_val = (betax - betax_target)**2 + \
              (betay - betay_target)**2 + \
              (alphax - alphax_target)**2 + \
              (alphay - alphay_target)**2
                
    obj_vec = np.array([betax - betax_target,
                        betay - betay_target,
                        alphax - alphax_target,
                        alphay - alphay_target])
    

    return obj_val, obj_vec
