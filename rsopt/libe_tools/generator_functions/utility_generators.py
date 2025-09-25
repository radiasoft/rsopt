import numpy as np
import logging
from rsopt.libe_tools.tools import _total_scan_entries


def generate_mesh(H, persis_info, gen_specs, libE_info):
    user_specs = gen_specs['user']
    exact_mesh = user_specs['exact_mesh']
    sampler_repeats = user_specs['sampler_repeats']

    # list of 1D arrays with the actual values for each parameter
    vectors: list[np.ndarray] = user_specs['vectors']

    # `groups` keys are just unique identifiers for the group.
    # groups items are a list of the 0-indexed placements of the parameter
    # in the list of parameters (matches with placement in `vectors`).
    # Need to preserve the order of the parameters from the config file
    # groups: dict[int or str, list[int]] = gen_specs['groups']
    groups: list[list[int]] = user_specs['groups']

    logger = logging.getLogger('libensemble')
    logger.debug('Generator called by Worker: {}'.format(libE_info['workerID']))

    if exact_mesh is None:
        size = _total_scan_entries(vectors, groups)
        # Must be object array to support the possibility of Categorical parameters
        value_mesh = np.zeros([size, len(vectors)]).astype('O')

        mesh_1d = []
        for group in groups:
            # All arrays in a group must have the same size to pass the config validator
            mesh_1d.append(np.arange(vectors[group[0]].size))

        # Mesh over the indices for each group
        index_mesh = np.meshgrid(*mesh_1d)
        index_mesh = np.array([ar.flatten() for ar in index_mesh]).T

        # For each row (point in the scan) fill in the actual parameter values (accounting for parameter groups)
        # corresponding to the integer indexing-mesh
        for i, row in enumerate(index_mesh):
            v_j = 0
            for j, val in enumerate(row):
                value_mesh[i, v_j:v_j+len(groups[j])] = [vectors[ii][val] for ii in groups[j]]
                v_j += len(groups[j])
    else:
        value_mesh = np.array(exact_mesh).T
    mesh = np.repeat(value_mesh, repeats=sampler_repeats, axis=0)

    out = np.zeros(mesh.shape[0], dtype=gen_specs['out'])
    logger.debug('mesh shape: {}'.format(mesh.shape))
    out['x'] = mesh.reshape(out['x'].shape)

    return out, persis_info
