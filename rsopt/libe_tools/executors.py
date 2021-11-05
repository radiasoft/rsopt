import os
import logging

from libensemble.executors.mpi_executor import MPIExecutor
from libensemble.executors.executor import Executor, Task, ExecutorException
from libensemble.resources.resources import Resources
from pykern import pkyaml
from rsopt import _EXECUTOR_SCHEMA

EXECUTOR_SCHEMA = pkyaml.load_file(_EXECUTOR_SCHEMA)
logger = logging.getLogger(__name__)
# To change logging level for just this module
# logger.setLevel(logging.DEBUG)

_RSMPI_CONFIG_PATH = EXECUTOR_SCHEMA['rsmpi']['config_path']


def register_rsmpi_executor(hosts='auto', cores_on_node=None, **kwargs):
    """
    Create an MPIExecutor that can use rsmpi. The executor is returned and may be used to register calculations
    for workers like any other libEnsemble executor.
    :param hosts: (str or int) If 'auto' then all rsmpi resources are detected and used. Otherwise specify number
                               of hosts as an int.
    :param cores_on_node: (tuple) Defaults to (16, 16). Number of physical cores and logical cores on the hosts.
    :param kwargs: Any other kwargs given will be passed to the MPIExecutor that is created.

    :return: libensemble.executors.mpi_executor.MPIExecutor object
    """
    schema = EXECUTOR_SCHEMA['rsmpi']

    if type(hosts) == int:
        hosts = int(hosts)
    elif type(hosts) == str:
        hosts = _detect_rsmpi_resources()
    else:
        raise TypeError('hosts must be str or int')

    _generate_rsmpi_node_file(hosts)

    customizer = {k:  schema[k] for k in ('mpi_runner', 'runner_name', 'subgroup_launch')}
    jobctrl = MPIExecutor(**kwargs, custom_info=customizer)
    # Set longer fail time - rsmpi is relatively slow to start
    jobctrl.fail_time = schema['fail_time']
    
    return jobctrl


def _detect_rsmpi_resources():
    hosts = 0
    assert os.path.isfile(_RSMPI_CONFIG_PATH), "rsmpi configuration does not exist"
    with open(_RSMPI_CONFIG_PATH, 'r') as ff:
        for line in ff.readlines():
            if 'Host' in line:
                hosts += 1

    assert hosts > 0, 'No hosts listed in rsmpi configuration'

    return hosts


def _generate_rsmpi_node_file(nodes):
    with open('libe_nodes', 'w') as ff:
        for node in range(1, nodes+1):
            ff.write(str(node)+'\n')


# Not strictly needed (MPIExecutor with n=1 is currently used by rsopt to simplify setup)
class SerialExecutor(Executor):
    def __init__(self):
        super().__init__()
        self._launch_with_retries = MPIExecutor._launch_with_retries
        self.max_launch_attempts = 5
        self.fail_time = 2
        self.retry_delay_incr = 5

    def add_comm_info(self, libE_nodes, serial_setup):
        """Adds comm-specific information to executor.
        Updates resources information if auto_resources is true.
        """
        self.resources.add_comm_info(libE_nodes=libE_nodes)
        # if serial_setup:
        #     self._serial_setup()

    def set_worker_info(self, comm, workerid=None):
        """Sets info for this executor"""
        self.workerID = workerid
        if not self.resources:
            self.resources = Resources()
        self.resources.set_worker_resources(self.workerID, comm)

    def submit(self, calc_type=None, app_name=None,
               app_args=None, stdout=None, stderr=None,
               dry_run=False, wait_on_start=False):
        if app_name is not None:
            app = self.get_app(app_name)
        elif calc_type is not None:
            app = self.default_app(calc_type)
        else:
            raise ExecutorException("Either app_name or calc_type must be set")
        default_workdir = os.getcwd()
        task = Task(app, app_args, default_workdir, stdout, stderr, self.workerID)
        runline = []
        runline.extend(task.app.full_path.split())
        if task.app_args is not None:
            runline.extend(task.app_args.split())
        task.runline = ' '.join(runline)  # Allow to be queried
        if dry_run:
            task.dry_run = True
            logger.info('Test (No submit) Runline: {}'.format(' '.join(runline)))
            task._set_complete(dry_run=True)
        else:
            # Launch Task
            self._launch_with_retries(task, runline, subgroup_launch=False, wait_on_start=wait_on_start)
            if not task.timer.timing:
                task.timer.start()
                task.submit_time = task.timer.tstart  # Time not date - may not need if using timer.
        self.list_of_tasks.append(task)
        return task
