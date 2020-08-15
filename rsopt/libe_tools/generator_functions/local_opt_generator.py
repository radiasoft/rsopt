"""
Run a local optimization method using a persistent generator.
This module makes use of the APOSMM local optimizer interface functions. The generator function contained
in this module was adapted from the persistent APOSMM generator as defined in:
https://github.com/Libensemble/libensemble/blob/a870bd4beffccbc863f79dfd7ab3940f2a57a269/libensemble/gen_funcs/persistent_aposmm.py
"""

from importlib import util
# TODO: If libEnsemble is updated can import optimizer list
# from libensemble.gen_funcs import aposmm_optimizer_list
aposmm_optimizer_list = ['petsc', 'nlopt', 'dfols', 'scipy', 'external']
available_opt = []
for optimizer in aposmm_optimizer_list:
    if optimizer == 'external':
        continue
    if util.find_spec(optimizer):
        print('found', optimizer)
        available_opt.append(optimizer)
    else:
        print(f'Package{optimizer} not installed. Will not be available.')

import libensemble.gen_funcs
libensemble.gen_funcs.rc.aposmm_optimizers = available_opt

import numpy as np
from libensemble.gen_funcs.aposmm_localopt_support import LocalOptInterfacer, ConvergedMsg, simulate_recv_from_manager

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG
from libensemble.tools.gen_support import send_mgr_worker_msg, get_mgr_worker_msg


def persistent_local_opt(H, persis_info, gen_specs, libE_info):
    try:
        # Setup
        user_specs = gen_specs['user']
        n, n_s, comm, local_H = initialize_local_opt(H, user_specs, libE_info)
        x_start = (user_specs['xstart']-user_specs['lb'])/(user_specs['ub']-user_specs['lb'])
        x_start = x_start.reshape(1, 2)  # x_start will be iterated over, should contain single row
        _, _, run_order, run_pts, total_runs, fields_to_pass = initialize_children(user_specs)

        # Intialize first point
        add_to_local_H(local_H, x_start, user_specs, local_flag=0, on_cube=True)
        # pass list of points in H (just one in our case)
        send_mgr_worker_msg(comm, local_H[[-1]][[i[0] for i in gen_specs['out']]])
        tag, Work, calc_in = get_mgr_worker_msg(comm)
        n_s, n_r = update_local_H_after_receiving(local_H, n, n_s, user_specs, Work, calc_in, fields_to_pass)

        # Start the local optimizer
        local_opter = LocalOptInterfacer(user_specs, x_start[0],
                                         local_H['f'] if 'f' in fields_to_pass else local_H['fvec'],
                                         local_H['grad'] if 'grad' in fields_to_pass else None)
        pass_to_local_opter = local_H[0][fields_to_pass]
        x_new = local_opter.iterate(pass_to_local_opter)
        add_to_local_H(local_H, x_new, user_specs, local_flag=1, on_cube=True)
        send_mgr_worker_msg(comm, local_H[[-1]][[i[0] for i in gen_specs['out']]])

        while True:
            tag, Work, calc_in = get_mgr_worker_msg(comm)
            if tag in [STOP_TAG, PERSIS_STOP]:
                clean_up_and_stop(local_opter)
                persis_info['run_order'] = run_order
                break
            n_s, n_r = update_local_H_after_receiving(local_H, n, n_s, user_specs, Work, calc_in, fields_to_pass)
            for row in calc_in:
                x_new = local_opter.iterate(row[fields_to_pass])
            if isinstance(x_new, ConvergedMsg):
                clean_up_and_stop(local_opter)
                persis_info['run_order'] = run_order
                break
            else:
                add_to_local_H(local_H, x_new, user_specs, local_flag=1, on_cube=True)
                send_mgr_worker_msg(comm, local_H[[-1]][[i[0] for i in gen_specs['out']]])

        return local_H, persis_info, FINISHED_PERSISTENT_GEN_TAG

    finally:
        try:
            clean_up_and_stop(local_opter)
        except NameError:
            pass


def initialize_children(user_specs):
    """ Initialize stuff for localopt children """
    local_opters = {}
    sim_id_to_child_inds = {}
    run_order = {}
    # run_pts can differ from 'x_on_cube'
    # if, for example, user_specs['periodic'] is True and run points are off the cube.
    run_pts = {}
    total_runs = 0
    if user_specs['localopt_method'] in ['LD_MMA', 'blmvm', 'scipy_BFGS']:
        fields_to_pass = ['x_on_cube', 'f', 'grad']
    elif user_specs['localopt_method'] in ['LN_SBPLX', 'LN_BOBYQA', 'LN_COBYLA', 'LN_NEWUOA',
                                           'LN_NELDERMEAD', 'scipy_Nelder-Mead', 'scipy_COBYLA',
                                           'external_localopt', 'nm']:
        fields_to_pass = ['x_on_cube', 'f']
    elif user_specs['localopt_method'] in ['pounders', 'dfols']:
        fields_to_pass = ['x_on_cube', 'fvec']
    else:
        raise NotImplementedError("Unknown local optimization method " "'{}'.".format(user_specs['localopt_method']))

    return local_opters, sim_id_to_child_inds, run_order, run_pts, total_runs, fields_to_pass


def add_to_local_H(local_H, pts, user_specs, local_flag=0, on_cube=True):
    """
    Adds points to O, the numpy structured array to be sent back to the manager
    """
    assert not local_flag or len(pts) == 1, "Can't > 1 local points"

    len_local_H = len(local_H)

    ub = user_specs['ub']
    lb = user_specs['lb']

    num_pts = len(pts)

    local_H.resize(len(local_H)+num_pts, refcheck=False)  # Adds num_pts rows of zeros to O

    if on_cube:
        local_H['x_on_cube'][-num_pts:] = pts
        local_H['x'][-num_pts:] = pts*(ub-lb)+lb
    else:
        local_H['x_on_cube'][-num_pts:] = (pts-lb)/(ub-lb)
        local_H['x'][-num_pts:] = pts

    if user_specs.get('periodic'):
        local_H['x_on_cube'][-num_pts:] = local_H['x_on_cube'][-num_pts:] % 1

    local_H['sim_id'][-num_pts:] = np.arange(len_local_H, len_local_H+num_pts)
    local_H['local_pt'][-num_pts:] = local_flag


def update_local_H_after_receiving(local_H, n, n_s, user_specs, Work, calc_in, fields_to_pass):

    for name in ['f', 'x_on_cube', 'grad', 'fvec']:
        if name in fields_to_pass:
            assert name in calc_in.dtype.names, name + " must be returned to persistent_aposmm for localopt_method: " + user_specs['localopt_method']

    for name in calc_in.dtype.names:
        local_H[name][Work['libE_info']['H_rows']] = calc_in[name]

    local_H['returned'][Work['libE_info']['H_rows']] = True
    n_s += np.sum(~local_H[Work['libE_info']['H_rows']]['local_pt'])
    n_r = len(Work['libE_info']['H_rows'])

    return n_s, n_r


def clean_up_and_stop(local_opter):
    local_opter.destroy()


def initialize_local_opt(H, user_specs, libE_info):
    """
    Computes common values every time that APOSMM is reinvoked

    .. seealso::
        `start_persistent_local_opt_gens.py <https://github.com/Libensemble/libensemble/blob/develop/libensemble/alloc_funcs/start_persistent_local_opt_gens.py>`_
    """
    n = len(user_specs['ub'])

    # rk_c = user_specs.get('rk_const', ((gamma(1+(n/2.0))*5.0)**(1.0/n))/sqrt(pi))
    # ld = user_specs.get('lhs_divisions', 0)
    # mu = user_specs.get('mu', 1e-4)
    # nu = user_specs.get('nu', 0)

    comm = libE_info['comm'] if not user_specs.get('standalone') else []

    local_H_fields = [('f', float),
                      ('grad', float, n),
                      ('x', float, n),
                      ('x_on_cube', float, n),
                      ('local_pt', bool),
                      ('sim_id', int),
                      ('paused', bool),
                      ('returned', bool),
                      ]

    if 'components' in user_specs:
        local_H_fields += [('fvec', float, user_specs['components'])]

    local_H = np.zeros(len(H), dtype=local_H_fields)

    if len(H):
        for field in H.dtype.names:
            local_H[field][:len(H)] = H[field]

        if user_specs['localopt_method'] in ['LD_MMA', 'blmvm']:
            assert 'grad' in H.dtype.names, "Must give 'grad' values to persistent_local_opt in gen_specs['in'] " \
                                            "when using 'localopt_method'" + user_specs['localopt_method']
            assert not np.all(local_H['grad'] == 0), "All 'grad' values are zero for the given points."

        assert 'f' in H.dtype.names, "Must give 'f' values to persistent_local_opt in gen_specs['in']"
        assert 'sim_id' in H.dtype.names, "Must give 'sim_id' to persistent_local_opt in gen_specs['in']"
        assert 'returned' in H.dtype.names, "Must give 'returned' status to persistent_local_opt in gen_specs['in']"

    n_s = np.sum(~local_H['local_pt'])

    if 'sample_points' in user_specs:
        assert isinstance(user_specs['sample_points'], np.ndarray)

    return n, n_s, comm, local_H