import matplotlib.pyplot as plt
from botorch.utils.multi_objective.pareto import is_non_dominated
import numpy as np
import torch


history_file = 'mobo_example_results.npy'
H = np.load(history_file)


plt.figure()
plt.xlabel('f1')
plt.ylabel('f2')

plt.scatter(H['f'][:, 0], H['f'][:, 1], label='evaluations')

valid_y = (H['c'][:, 0] > 0) * (H['c'][:, 1] < 0.5)
non_dom = is_non_dominated(torch.from_numpy(-H['f'][valid_y]))
plt.scatter(H['f'][valid_y, 0][non_dom],
            H['f'][valid_y, 1][non_dom], label='non-dominated')

plt.legend()

plt.savefig('tnk_optimization_result.pdf')
plt.show()