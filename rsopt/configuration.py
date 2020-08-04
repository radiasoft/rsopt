from numpy import ndarray
# FUTURE: Setup load / dump of YAML configuration files
# FUTURE: Is there relevant code to move from `Runner`? Certainly some of configuration code will be
#   used by runner


_EXTERNAL_PARAMETER_CATEGORIES = ('min', 'max', 'start')


def read_parameter_array(obj):
    """
    Read an array of N parameters with rows organized by either
    (name, min, max start) or (min, max, start)
    :param input:
    :return:
    """

    for i, row in enumerate(obj):
        if len(row) == 4:
            yield row[0], row.tolist()[1:]
        else:
            raise IndexError("Input parameters are no length 3 or 4")


def read_parameter_dict(obj):
    for name, values in obj.items():
        output = []
        for key in _EXTERNAL_PARAMETER_CATEGORIES:
            output.append(values[key])
        yield name, output


_PARAMETER_READERS = {
    ndarray: read_parameter_array,
    dict: read_parameter_dict
}


class Parameters:
    def __init__(self):
        self.pararameters = {}
        self._NAMES = []
        self._LOWER_BOUND = 'lb'
        self._UPPER_BOUND = 'ub'
        self._START = 'start'
        self.fields = (self._LOWER_BOUND, self._UPPER_BOUND, self._START)

    def parse_parameters(self, name, values):
        self._NAMES.append(name)
        self.pararameters[name] = {}
        for field, value in zip(self.fields, values):
            self.pararameters[name][field] = value

    def get_lower_bound(self):
        return [self.pararameters[name][self._LOWER_BOUND] for name in self._NAMES]

    def get_upper_bound(self):
        return [self.pararameters[name][self._UPPER_BOUND] for name in self._NAMES]

    def get_start(self):
        return [self.pararameters[name][self._START] for name in self._NAMES]


def read_setting_dict(input):
    for name, values in input.items():
        yield name, values


_SETTING_READERS = {
    dict: read_setting_dict
}


class Settings:
    def __init__(self):
        self.settings = {}

    def parse_settings(self, name, value):
        self.settings[name] = value


def get_reader(obj, category):
    config_categories = {'parameters': _PARAMETER_READERS,
                         'settings': _SETTING_READERS}
    obj_type = type(obj)

    return config_categories[category][obj_type]
