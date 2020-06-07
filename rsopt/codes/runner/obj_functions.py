import numpy as np
from scipy.constants import c as clight


def dummy(H):
    return 0


def calculate_emittance(bunch):
    x = bunch.x
    xp = bunch.ux
    y = bunch.y
    yp = bunch.uy
    
    enx = np.sqrt(np.average(x**2) * np.average(xp**2) - np.average(x * xp)**2)
    eny = np.sqrt(np.average(y**2) * np.average(yp**2) - np.average(y * yp)**2)
    
    return enx, eny
        

def simple_objective_f(H):
    print("switchyard file", H['switchyard'].input_file)
    bunch = H['switchyard'].species['Species_0']
    if bunch.pt.size < 1:
        print('All particles lost')
        return 50000.
    
    enx, eny = calculate_emittance(bunch)
    sigma_p = np.std(bunch.pt)
    sigma_t = np.std(bunch.ct / clight)
    print('Emitt weighted', enx * 1e6, eny*1e6)
    print('Sigma_p weighted', sigma_p * 1.)
    print('Sigma_t weighted', sigma_t * 1e13)
    print('{} particles remaining out of 50,000'.format(bunch.pt.size))
    return (sigma_p * 1. + sigma_t * 1e13 + (enx + eny) * 1e6) * 50e3 / bunch.pt.size