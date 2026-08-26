"""Plot the Py-BOBYQA search trajectories of the Himmelblau example.

Run the example first, then this script from the same directory::

    rsopt optimize configuration config_pybobyqa.yml
    python plot_trajectories.py

"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, LogNorm
from rsopt import parse
from rsopt.libe_tools.analysis import load_results
from himmelblau import himmelblau

CONFIG = 'config_pybobyqa.yml'
OUTPUT = 'pybobyqa_trajectories.png'
INSTANCE_COLORS = ['#2a78d6', '#eb6834', '#1baf7a']

### Load and Set Data ###

results = load_results('.')
config = parse.parse_optimize_configuration(parse.read_configuration_file(CONFIG))

# `x` and `y` are the parameter names given in the configuration file. `instance` is written to the
# history by the Py-BOBYQA generator and says which of the independent searches asked for a point.
x = results.gather('x')
y = results.gather('y')
f = results.gather('f')
instance = results.gather('instance')
sim_id = results.gather('sim_id')

lower_bounds, upper_bounds = config.lower_bounds, config.upper_bounds
grid_x, grid_y = np.meshgrid(np.linspace(lower_bounds[0], upper_bounds[0], 400),
                             np.linspace(lower_bounds[1], upper_bounds[1], 400))
surface = himmelblau(grid_x, grid_y)


### PLOTTING ###

levels = np.logspace(0.0, np.log10(surface.max()), 20)
# Only the pale end of the colormap, to keep the trajectories legible on top of the surface.
surface_colors = ListedColormap(plt.get_cmap('Greys')(np.linspace(0.0, 0.62, 256)))

fig, ax = plt.subplots(figsize=(7, 6))
filled = ax.contourf(grid_x, grid_y, surface, levels=levels, norm=LogNorm(), extend='min',
                     cmap=surface_colors)

for i, color in enumerate(INSTANCE_COLORS):
    selected = instance == i
    # Sort by sim_id: workers return points as they finish, so history order is not search order.
    order = np.argsort(sim_id[selected])
    path_x, path_y = x[selected][order], y[selected][order]
    best = np.argmin(f[selected][order])

    ax.plot(path_x, path_y, color=color, linewidth=1.5, marker='o', markersize=3,
            label=f'instance {i}')
    ax.plot(path_x[0], path_y[0], color=color, marker='o', markersize=11,
            markeredgecolor='white', markeredgewidth=1.2)
    ax.plot(path_x[best], path_y[best], color=color, marker='*', markersize=16,
            markeredgecolor='white', markeredgewidth=1.0)

ax.plot([], [], color='0.3', marker='o', markersize=11, linestyle='none', label='start')
ax.plot([], [], color='0.3', marker='*', markersize=16, linestyle='none', label='best point')

ax.set_xlim(lower_bounds[0], upper_bounds[0])
ax.set_ylim(lower_bounds[1], upper_bounds[1])
ax.set_aspect('equal')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title("Py-BOBYQA searches on Himmelblau's function")
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=5, frameon=False)

colorbar = fig.colorbar(filled, ax=ax, ticks=[1, 10, 100, surface.max()], format='%.0f')
colorbar.set_label('f(x, y)')

fig.tight_layout()
fig.savefig(OUTPUT, dpi=150)
print(f'wrote {OUTPUT}')
