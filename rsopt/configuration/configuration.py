from rsopt.configuration import Options


class Configuration:
    def __init__(self):
        self.jobs = []
        self._options = None

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, options):
        new_options = Options.get_option(options)
        new_options.parse()

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