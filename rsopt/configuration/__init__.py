from rsopt.configuration.parameters import _PARAMETER_READERS, Parameters
from rsopt.configuration.settings import _SETTING_READERS, Settings
from rsopt.configuration.setup import _SETUP_READERS, Setup
from rsopt.configuration.configuration import Configuration
from rsopt.configuration.jobs import Job

def get_reader(obj, category):
    config_categories = {'parameters': _PARAMETER_READERS,
                         'settings': _SETTING_READERS,
                         'setup': _SETUP_READERS}
    obj_type = type(obj)

    return config_categories[category][obj_type]