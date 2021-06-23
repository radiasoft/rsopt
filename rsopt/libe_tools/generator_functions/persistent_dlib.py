import numpy as np
import dlib

import logging
logger = logging.getLogger()

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG
from libensemble.tools.gen_support import send_mgr_worker_msg, get_mgr_worker_msg

# Be careful: dlib seems to automatically truncate printout of values in many places,
# but passes floats to full precision


def persistent_dlib(H, persis_info, gen_specs, libE_info):

    # libEnsemble Setup
    local_H = np.zeros(len(H), dtype=H.dtype)
    libE_comm = libE_info['comm']

    dim = gen_specs['user']['dim']
    # dlib requires lists for bounds
    lb = list(gen_specs['user']['lb'])
    ub = list(gen_specs['user']['ub'])
    num_workers = gen_specs['user']['workers']
    print(f'dlib will be giving out values for {num_workers} workers')

    opt_spec = dlib.function_spec(lb, ub)
    opt = dlib.global_function_search([opt_spec, ])

    # get initial points
    work_log = {}
    work_requests = []
    for i in range(num_workers):
        # Pass dlib's `function_evaluation_request` object
        # This has methods for getting (`function_evaluation_request.x`) the point to be evaluated and
        #  setting (`function_evaluation_request.set`) the return value
        request = opt.get_next_x()
        work_requests.append(request)
    add_to_local_H(local_H, work_requests, work_log)
    send_mgr_worker_msg(libE_comm, local_H[-len(work_requests):][[i[0] for i in gen_specs['out']]])

    # Start work loop
    while True:
        # Get results back from libE workers
        tag, Work, calc_in = get_mgr_worker_msg(libE_comm)
        if tag in [STOP_TAG, PERSIS_STOP]:
            break

        work_requests = []
        for row in calc_in:
            request = work_log.pop(row['sim_id'])
            # Pass negative - By default `global_function_search` seeks to maximize the return value
            request.set(-row['f'])
            work_requests.append(opt.get_next_x())
            # Send new points to allocator - if any

        if work_requests:
            add_to_local_H(local_H, work_requests, work_log)
            send_mgr_worker_msg(libE_comm, local_H[-len(work_requests):][[i[0] for i in gen_specs['out']]])
    # TODO: Result of Last point evaluated is not always being recorded in H before termination
    return local_H, persis_info, FINISHED_PERSISTENT_GEN_TAG


def separate_data_in(data):
    x_vals = []
    for datum in data:
        x_vals.append(datum.x)

    return x_vals


def add_to_local_H(local_H, points, log):
    x = separate_data_in(points)
    len_local_H = len(local_H)
    num_pts = len(points)

    # TODO: Is this needed? I thought local_H is sized to H when created.
    local_H.resize(len(local_H)+num_pts, refcheck=False)  # Adds num_pts rows of zeros to O
    local_H['x'][-num_pts:] = x
    local_H['sim_id'][-num_pts:] = np.arange(len_local_H, len_local_H+num_pts)

    for sim_id, request in zip(local_H['sim_id'][-num_pts:], points):
        log[sim_id] = request

