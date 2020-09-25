import subprocess
import numpy as np
from rsbeams.rsdata.SDDS import readSDDS

def obj_f(_):

    analysis_command = ["sddsanalyzebeam", "run_setup.output.sdds", "output.anb"]
    subprocess.call(analysis_command)

    anb = readSDDS("output.anb")
    anb.read()

    betax, betax_target = anb.columns['betax'].squeeze(), 18.
    betay, betay_target = anb.columns['betay'].squeeze(), 20.
    alphax, alphax_target = anb.columns['alphax'].squeeze(), -1.
    alphay, alphay_target = anb.columns['alphay'].squeeze(), -1.

    obj_val = np.sqrt((betax - betax_target)**2 +
                      (betay - betay_target)**2 +
                      (alphax - alphax_target)**2 +
                      (alphay - alphay_target)**2)

    return obj_val
