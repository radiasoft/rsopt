import numpy as np
import logging


def generate_mesh(H, persis_info, gen_specs, libE_info):
    user_specs = gen_specs['user']
    mesh_specs = user_specs['mesh_definition']
    exact_mesh = user_specs['exact_mesh']
    
    logger = logging.getLogger()
    logging.info('Generator called by Worker', libE_info['workerID'])
    
    if not exact_mesh:
        mesh_1d = []
        for dim in mesh_specs:
            mesh_1d.append(np.linspace(*dim))
        mesh = np.meshgrid(*mesh_1d)
        mesh = np.array([ar.flatten() for ar in mesh]).T
    else:
        mesh = np.array(mesh_specs).T

    out = np.zeros(mesh.shape[0], dtype=gen_specs['out'])
    out['x'] = mesh.squeeze()

    return out, persis_info
