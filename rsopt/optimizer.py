from rsopt.configuration import Configuration, Job
from rsopt.parse import read_configuration_file, parse_yaml_configuration
from pykern.pkcollections import PKDict
from os import path
import numpy as np


_NAME = None

OPTIONS_ALLOWED = {'record_interval': {'libEnsemble': ['libE_specs', 'save_every_k_sims']},
                   'working_directory': {'libEnsemble': ['libE_specs', 'ensemble_dir_path']}
                   }


class Optimizer:
    name = _NAME

    def __init__(self):
        self._config = Configuration()
        self.gen_specs = {}
        self.dimension = 0
        self.optimizer_method = ''
        self._options = {}

        self.recording_method = None
        self.exit_criteria = None
        self.function = None
        self.executable = None

    @property
    def lb(self):
        return self._config.get_parameters_list('get_lower_bound', formatter=np.array)

    @lb.setter
    def lb(self, value=None):
        pass

    @property
    def ub(self):
        return self._config.get_parameters_list('get_upper_bound', formatter=np.array)

    @ub.setter
    def ub(self, value=None):
        pass

    @property
    def start(self):
        return self._config.get_parameters_list('get_start', formatter=np.array)

    @start.setter
    def start(self, value=None):
        pass

    def load_configuration(self, config):
        """
        Load a configuration file to setup an optimization run.
        May be given as a dictionary or path to configuration stored in YAML format

        :param config: (dict or PKDict or str) The configuration file definition or path to the file
        :return: None
        """
        if isinstance(config, dict) or isinstance(config, PKDict):
            parse_yaml_configuration(config, self._config)
        elif isinstance(config, Configuration):
            self._config = config
        elif path.exists(config):
            config = read_configuration_file(config)
            parse_yaml_configuration(config, self._config)
        else:
            raise TypeError('Configuration was not readable')

    def _set_dimension(self):
        if self._config.get_dimension() == 0:
            print("Warning: Cannot set dimension. No parameters have been set.")
        else:
            self.dimension = self._config.get_dimension()

    def set_parameters(self, parameters, job=0):
        assert job < len(self._config.jobs), f"Job with index {job} cannot be found"
        self._config.jobs[job].parameters = parameters

    def set_settings(self, settings, job=0):
        assert job < len(self._config.jobs), f"Job with index {job} cannot be found"
        self._config.jobs[job].settings = settings

    def set_exit_criteria(self, exit_criteria):
        # TODO: Will override in sublcasses probably
        self.exit_criteria = exit_criteria

    def _set_recording(self):
        if self.recording_method:
            self.recording_method()

    def _manual_job_setup(self):
        # if Optimizer is being setup manually then only one job is allowed
        # Running with a multi job chain must be setup through a config file
        self._config.set_jobs(Job())

