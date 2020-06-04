import numpy as np
import logging

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG
from libensemble.tools.gen_support import send_mgr_worker_msg
from libensemble.tools.gen_support import get_mgr_worker_msg
"""
    def run_pso(self, function, searchspace, target, nparticles, maxiter, precision, domain, verbose=True):

        Performs a PSO for the given function in the searchspace, looking for the target, which is in the output space.
        
        function - the function to be optimized. Its domain must include the seachspace and its output must be in the space of target.
        searchspace - np.array((ssdim, 2)) 
        target - np.array((tdim, ))
        nparticles - number of particles to use in the optimization
        maxiter - maximum number of iterations to the optimization routine
        precision - how close to the target to attemp to get
        domain - absolute boundaries on the trial solutions/particles
"""


def persistant_pso(H, persis_info, gen_specs, libE_info):
    """


    - ``'x' [n floats]``: Parameters being optimized over
    - ``'x_on_cube' [n floats]``: Parameters scaled to the unit cube
    - ``'f' [float]``: Objective function being minimized


    - ``'num_active_runs' [int]``: Number of active local runs point is in

    - ``'sim_id' [int]``: Row number of entry in history

    gen_specs['user'] should supply the following:

    nparticles: Number of particles in the optimizer swarm
    lb: lower bound of the search domain
    ub: upper bound of the search domain

    optionally the user may supply:

    initial_sample_points: A set of points to start the particles. initial_sample_points must be <= nparticles if given.

    :param H:
    :param persis_info:
    :param gen_specs:
    :param libE_info:
    :return:
    """

    user_specs = gen_specs['user']

    try:
        assert user_specs['initial_sample_points'].shape[0] <= user_specs['nparticles'], \
            "initial_sample_points must be <= nparticles"
    except KeyError:
        user_specs['initial_sample_points'] = 0

    if user_specs['initial_sample_points'] != 0:
        # Send our initial sample. We don't need to check that n_s is large enough:
        # the alloc_func only returns when the initial sample has function values.
        persis_info = add_k_sample_points_to_local_H(user_specs['initial_sample_points'], user_specs,
                                                     persis_info, n, local_H)
        send_mgr_worker_msg(comm, local_H[-user_specs['initial_sample_size']:][[i[0] for i in gen_specs['out']]])
        something_sent = True
    else:
        something_sent = False


def add_k_sample_points_to_local_H(k, user_specs, persis_info, n, local_H):

    if 'sample_points' in user_specs:
        v = np.sum(~local_H['local_pt'])  # Number of sample points so far
        sampled_points = user_specs['sample_points'][v:v+k]
        on_cube = False  # Assume points are on original domain, not unit cube
        if len(sampled_points):
            add_to_local_H(local_H, sampled_points, user_specs, on_cube=on_cube)
        k = k-len(sampled_points)

    if k > 0:
        sampled_points = persis_info['rand_stream'].uniform(0, 1, (k, n))
        add_to_local_H(local_H, sampled_points, user_specs, on_cube=True)

    return persis_info


