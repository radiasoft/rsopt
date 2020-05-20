import numpy as np


def generate_mesh(H, persis_info, gen_specs, libE_info):
    user_specs = gen_specs['user']
    mesh_specs = user_specs['mesh_definition']

    print('Generator called by Worker',libE_info['workerID'])

    mesh_1d = []
    for dim in mesh_specs:
        mesh_1d.append(np.linspace(*dim))
    mesh = np.meshgrid(*mesh_1d)
    mesh = np.array([ar.flatten() for ar in mesh]).T

    out = np.zeros(mesh.shape[0], dtype=gen_specs['out'])
    out['x'] = mesh

    return out, persis_info
