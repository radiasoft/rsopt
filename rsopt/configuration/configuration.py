class Configuration:
    def __init__(self):
        self.jobs = []
        self.options = {}

    def set_jobs(self, jobs):
        self.jobs.extend(jobs)

    def get_formatted_parameters_list(self, attribute, formatter=list):
        # get list attribute from all job parameters and return based on formatter
        attribute_list = []
        for job in self.jobs:
            attribute_list.extend(*job.__getattribute__(attribute))

        return formatter(*attribute_list)