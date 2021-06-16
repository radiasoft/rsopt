from multiprocessing import Event, Process, Queue
import numpy as np


from poap.controller import ThreadController, ProcessWorkerThread
from pySOT.experimental_design import SymmetricLatinHypercube
from pySOT.strategy import SRBFStrategy
from pySOT.surrogate import CubicKernel, LinearTail, RBFInterpolant
from pySOT.optimization_problems import OptimizationProblem

import logging
logger = logging.getLogger()

from libensemble.message_numbers import STOP_TAG, PERSIS_STOP, FINISHED_PERSISTENT_GEN_TAG
from libensemble.tools.gen_support import send_mgr_worker_msg, get_mgr_worker_msg


class Problem(OptimizationProblem):
    def __init__(self, dim, lb, ub):
        self.dim = dim
        self.lb = lb
        self.ub = ub

        self.int_var = np.array([])
        self.cont_var = np.arange(0, dim)
        self.info = ''

    def eval(self, _):
        pass


class Manager(ProcessWorkerThread):

    #     communicator = communicator_pysot

    def __init__(self, controller, comm_queue, parent_can_read, child_can_read, my_id):
        super().__init__(controller)
        self.local_comm_queue = comm_queue
        self.local_parent_can_read = parent_can_read
        self.local_child_can_read = child_can_read
        self.local_id = my_id

    def handle_eval(self, x):
        f = communicator_pysot(x.params, self.local_id, self.local_comm_queue, self.local_parent_can_read, self.local_child_can_read)
        self.finish_success(x, f)


def run_pysot_in_process(dim, lb, ub, max_evals, num_pts, num_threads, comm_queues, parent_can_read, child_can_read):
    # pySOT Setup
    # sys.stdout = open(str(os.getpid()) + ".out", "w")
    # sys.stderr = open(str(os.getpid()) + ".err", "w")

    strategy_manager = Problem(dim, lb, ub)

    rbf = RBFInterpolant(dim=dim, lb=lb, ub=ub, kernel=CubicKernel(), tail=LinearTail(dim))
    slhd = SymmetricLatinHypercube(dim=dim, num_pts=num_pts)
    # Create a strategy and a controller
    controller = ThreadController()
    controller.strategy = SRBFStrategy(
        max_evals=max_evals, opt_prob=strategy_manager, exp_design=slhd, surrogate=rbf, asynchronous=True
    )

    # Launch the threads and give them access to the objective function
    for i in range(num_threads):
        controller.launch_worker(Manager(controller, comm_queues[i], parent_can_read[i], child_can_read[i], i))

    controller.run()


def persistent_pysot(H, persis_info, gen_specs, libE_info):

    # libEnsemble Setup
    libE_comm = libE_info['comm']

    dim = gen_specs['user']['dim']
    lb = gen_specs['user']['lb']
    ub = gen_specs['user']['ub']
    # pySOT causes problems terminating - setting max evals to always be larger by the thread count
    #  should guarantee that pySOT will run until libEnsemble stops the process
    max_evals = gen_specs['user']['max_evals'] + gen_specs['user']['threads']
    num_pts = gen_specs['user'].get('num_pts') or 2 * (dim + 1)
    num_threads = gen_specs['user']['threads']

    # Communication Setup
    comm_queues, parent_can_read, child_can_read = [], [], []
    for i in range(num_threads):
        new_queue = Queue()
        comm_queues.append(new_queue)

        parent_read_event = Event()
        parent_can_read.append(parent_read_event)

        child_read_event = Event()
        child_can_read.append(child_read_event)

    # Start pySOT
    print('Starting pySOT optimization')
    result = Process(target=run_pysot_in_process, args=(dim, lb, ub, max_evals, num_pts, num_threads,
                                                        comm_queues, parent_can_read, child_can_read,))
    result.start()
    try:
        # Initialize Worker communication and Begin
        local_H = np.zeros(len(H), dtype=H.dtype)
        # Stores assignments of sim_id to thread Manager ID
        thread_log = {}
        start_data = []  # Entries are tuples of (x, thread_id)

        # Get initial round of points from all pySOT threads
        for i in range(num_threads):
            data_in = get_pysot_point(comm_queues[i])
            start_data.append(data_in)

        add_to_local_H(local_H, start_data, thread_log)
        send_mgr_worker_msg(libE_comm, local_H[-len(start_data):][[i[0] for i in gen_specs['out']]])

        # Start work loop
        while True:
            # Get results back from libE workers
            tag, Work, calc_in = get_mgr_worker_msg(libE_comm)
            if tag in [STOP_TAG, PERSIS_STOP]:
                result.terminate()
                break

            # Send all results to pySOT that we got from libE workers
            data_for_workers = []
            for row in calc_in:
                thread_id = thread_log.pop(row['sim_id'])
                # threads are started sequentially so their id is the index in comm lists
                give_pysot_result(row['f'], comm_queues[thread_id],
                                  parent_can_read[thread_id], child_can_read[thread_id])
                # get new point to evaluate from the thread
                data_in = get_pysot_point(comm_queues[thread_id])
                data_for_workers.append(data_in)

            # Send new points to allocator - if any
            if data_for_workers:
                add_to_local_H(local_H, data_for_workers, thread_log)
                send_mgr_worker_msg(libE_comm, local_H[-len(data_for_workers):][[i[0] for i in gen_specs['out']]])

        return local_H, persis_info, FINISHED_PERSISTENT_GEN_TAG
    finally:
        result.terminate()


def separate_data_in(data):
    x_vals, id_vals = [], []
    for datum in data:
        x, id = datum
        x_vals.append(x)
        id_vals.append(id)

    return x_vals, id_vals


def add_to_local_H(local_H, points, log):
    x, ids = separate_data_in(points)
    len_local_H = len(local_H)
    num_pts = len(points)

    local_H.resize(len(local_H)+num_pts, refcheck=False)  # Adds num_pts rows of zeros to O
    local_H['x'][-num_pts:] = x
    local_H['sim_id'][-num_pts:] = np.arange(len_local_H, len_local_H+num_pts)

    for sim_id, id, in zip(local_H['sim_id'][-num_pts:], ids):
        log[sim_id] = id


def get_pysot_point(comm_queue):
    """This function gets messages from the pySOT communicator for the generator"""
    return comm_queue.get()


def give_pysot_result(f, comm_queue, parent_can_read, child_can_read):
    """This function gives messages from the generator to the pySOT thread"""
    parent_can_read.clear()

    comm_queue.put(f)

    child_can_read.set()
    parent_can_read.wait()


def communicator_pysot(x, my_id, comm_queue, parent_can_read, child_can_read):
    """This communicator is used by pySOT handle_eval to send messages out to the main generator process"""
    print(f"{my_id} is putting a value in the queue")
    comm_queue.put((x[0], my_id))
    print(f"{my_id} has told the parent to read")
    parent_can_read.set()
    print(f"{my_id} is going to wait")
    child_can_read.wait()
    print(f"{my_id} is free")
    values = comm_queue.get()
    print(f"{my_id} got back", values)
    child_can_read.clear()

    return values
