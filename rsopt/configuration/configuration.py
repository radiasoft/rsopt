from rsopt.configuration import Options
from rsopt.configuration.setup import _EXECUTION_TYPES
_EXECUTORS = {'parallel'}


class Configuration:

    def __init__(self):
        self.jobs = []
        self._options = Options()
        self.comms = 'local'  # Will be either local or mpi
        self.mpi_comm = None
        self.is_manager = True
        # self.rsmpi_executor = False  # Is set to true if any executor uses rsmpi

    @property
    def options(self):
        return self._options

    @property
    def rsmpi_executor(self):
        rsmpi_used = any([j.setup.get('execution_type') == 'rsmpi' for j in self.jobs if j.setup.get('execution_type')])
        return rsmpi_used

    def parameters(self, job=0):
        assert self.jobs[job], f"Requested job: {job} is not registered in the Configuration"

        return self.jobs[job].parameters

    def settings(self, job=0):
        assert self.jobs[job], f"Requested job: {job} is not registered in the Configuration"

        return self.jobs[job].settings

    def setup(self, job=0):
        assert self.jobs[job], f"Requested job: {job} is not registered in the Configuration"

        return self.jobs[job].setup

    @options.setter
    def options(self, options):
        new_options = self._options.get_option(options)()
        for name, value in options.items():
            new_options.parse(name, value)
        self._options = new_options

    @property
    def method(self):
        return self._options.method
    @property
    def software(self):
        return self._options.NAME

    def set_jobs(self, jobs):
        if hasattr(jobs, '__iter__'):
            self.jobs.extend(jobs)
        else:
            self.jobs.append(jobs)

    def get_dimension(self):
        dim = 0
        for job in self.jobs:
            dim += len(job.parameters)

        return dim

    def get_parameters_list(self, attribute, formatter=list):
        # get list attribute from all job parameters and return based on formatter
        attribute_list = []
        for job in self.jobs:
            attribute_list.extend(job._parameters.__getattribute__(attribute)())

        return formatter(attribute_list)

    # TODO: Shifter needs special handling, it is still MPIExecutor but needs to change app setup
    def create_exector(self):
        # Executor is created even for serial jobs
        # For serial Python the executor is not registerd with the Job and goes unused

        # rsmpi is the only mutually exclusive option right now
        executors = [j.setup.get('execution_type') for j in self.jobs if j.setup.get('execution_type')]
        if executors.count('rsmpi') != len(executors) and executors.count('rsmpi') != 0:
            raise NotImplementedError("rsmpi is not supported in combination with other executors")

        # Right now we implicitly guarantee all executors will be same type
        executor = _EXECUTION_TYPES[executors[0]]

        return executor(**self.options.executor_options)

    def get_sym_link_list(self):
        sym_link_files = []
        for job in self.jobs:
            if job.code == 'python' and job.setup.get('input_file'):
                # If an input file is registered then copy to run dir, otherwise expect Python function defined or
                # imported into input script
                sym_link_files.append(job.setup['input_file'])

            if job.code == 'user':
                if job.setup['input_file'] not in job.setup['file_mapping'].values():
                    # If file name in file_mapping then input_file being created dynamically, otherwise copy here
                    sym_link_files.append(job.setup['input_file'])

            # TODO: Genesis currently handles its own symlinking which is inconsistent with the usage here
            #       Should be changed to use the configuration symlink method and let libEnsemble handle

        # Add user specified file names
        sym_link_files.extend(self._options.sym_links)

        return sym_link_files

