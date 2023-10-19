from rsopt.configuration import Options
from rsopt.configuration import parameters
from rsopt.configuration import settings
from rsopt.configuration.setup import setup
from rsopt.configuration.setup import EXECUTION_TYPES
_EXECUTORS = {'parallel'}


class Configuration:
    """
    Stores Job and Option data for a run and provides interfaces to data that requires knowledge of the state
    of all Jobs together or the combined state of Jobs and Options.

    For information on individual Jobs and Options states, the respective objects are queried directly.
    """

    def __init__(self):
        self.jobs = []
        self._options = Options()
        self.comms = 'local'  # Will be either local or mpi
        self.mpi_comm = None
        self.is_manager = True
        self.configuration_file = ''
        # self.rsmpi_executor = False  # Is set to true if any executor uses rsmpi

    @property
    def options(self) -> Options:
        """
        Getter
        :return: Options object for the configuration
        """
        return self._options

    @property
    def rsmpi_executor(self) -> bool:
        """
        Is rsmpi used for any Job in the Job list
        """
        rsmpi_used = any([j.setup.get('execution_type') == 'rsmpi' for j in self.jobs if j.setup.get('execution_type')])
        return rsmpi_used

    def parameters(self, job: int = 0) -> parameters.Parameters:
        """
        Getter
        :param job: Index of Job in job list
        :return: Parameters object
        """
        assert self.jobs[job], f"Requested job: {job} is not registered in the Configuration"

        return self.jobs[job].parameters

    def settings(self,  job: int = 0) -> settings.Settings:
        """
        Getter
        :param job: Index of Job in job list
        :return: Settings object
        """
        assert self.jobs[job], f"Requested job: {job} is not registered in the Configuration"

        return self.jobs[job].settings

    def setup(self,  job: int = 0) -> setup.Setup:
        """
        Getter
        :param job:  Index of Job in job list
        :return: Setup object
        """
        assert self.jobs[job], f"Requested job: {job} is not registered in the Configuration"

        return self.jobs[job].setup

    @options.setter
    def options(self, options: dict) -> None:
        # Iterates through a dictionary to set up an Options object from that dictionary
        new_options = self._options.get_option(options)()
        for name, value in options.items():
            new_options.parse(name, value)
        self._options = new_options

    @property
    def method(self) -> str:
        """
        Get name of the method (if any) to be used with software
        :return:
        """
        return self._options.method

    @property
    def software(self) -> str:
        """
        Get name of Options class (software from configuration file)
        :return:
        """
        return self._options.NAME

    def set_jobs(self, jobs):
        if hasattr(jobs, '__iter__'):
            self.jobs.extend(jobs)
        else:
            self.jobs.append(jobs)

    def get_dimension(self) -> int:
        """
        Calculate the parameter space dimension
        :return:
        """
        dim = 0
        for job in self.jobs:
            dim += len(job.parameters)

        return dim

    def get_parameters_list(self, attribute: str, formatter=list):
        """
        Iterate through jobs and assemble shared attributes into a single iterable object.
        :param attribute: attribute to query
        :param formatter: (list) iterable container to put attributes in. Must have method `extend`.
        :return: iterable with type from `formatter`
        """
        # get list attribute from all job parameters and return based on formatter
        attribute_list = []
        for job in self.jobs:
            attribute_list.extend(job._parameters.__getattribute__(attribute)())

        return formatter(attribute_list)

    def sim_dirs_required(self) -> bool:
        # If a job requires individual sim directories to make input files then set sim_dirs_make = True
        # we choose to always set use_worker_dirs = True in this case, but this is not strictly required
        # If no job requires sim_dirs_make then we check options for the settings

        for job in self.jobs:
            if job.sim_dirs_required:
                return True
        return False

    # TODO: Shifter needs special handling, it is still MPIExecutor but needs to change app setup
    def create_exector(self):
        # Executor is created even for serial jobs
        # For serial Python the executor is not registerd with the Job and goes unused

        # rsmpi is the only mutually exclusive option right now
        executors = [j.setup.get('execution_type') for j in self.jobs if j.setup.get('execution_type')]
        if executors.count('rsmpi') != len(executors) and executors.count('rsmpi') != 0:
            raise NotImplementedError("rsmpi is not supported in combination with other executors")

        # Right now we implicitly guarantee all executors will be same type
        executor = EXECUTION_TYPES[executors[0]]

        return executor(**self.options.executor_options)

    def get_sym_link_list(self) -> list:
        # TODO: Genesis currently handles its own symlinking which is inconsistent with the usage here
        #       Should be changed to use the configuration symlink method and let libEnsemble handle

        sym_link_files = set()
        for job in self.jobs:
            sym_link_files.update(job.sym_link_targets)
            # Each flash simulation may be a unique executable and will not be in PATH
            if job.code == 'flash':
                sym_link_files.add(job.setup['executable'])
        sym_link_files.update(self._options.sym_links)

        return list(sym_link_files)

