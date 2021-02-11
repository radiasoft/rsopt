import numpy as np
import matplotlib.pyplot as plt

# NOTE: File name will change depending on settings
H = np.load('H_sample_rsop_scan_width_history_length=12_evals=12_workers=3.npy')
# H (history file) is a structured numpy array containing information on the scan execution and results
# Input parameters are stored in the field `x` and results of the scan 
# (if they were passed back to rsopt) will be in `f`

# Ordering of points  is not guaranteed because of the asynchronous evaluation of points in the scan
order = np.argsort(H['x'])

# Plotting
plt.figure()
plt.plot(H['x'][order], H['f'][order])
plt.xlabel('Pole Width (cm)')
plt.ylabel('$B_z$ (T)')
plt.savefig('pole_width_scan.png')