from numpy import ndarray
import numpy as np
from pykern.pkcollections import PKDict

_EXTERNAL_PARAMETER_CATEGORIES = ('min', 'max', 'start')
_OPTIONAL_PARAMETER_CATEGORIES = ('samples', )


def _validate_parameter(name, min, max, start):
    assert min < max, f"Parameter {name} invalid: min > max"
    assert min <= start <= max, f"Parameter {name} invalid: start is not between [min,max]"


def read_parameter_array(obj):
    """
    Read an array of N parameters with rows organized by either
    (name, min, max start) or (name, min, max, start, samples)
    :param input:
    :return:
    """

    for i, row in enumerate(obj):
        if len(row) == 5:
            yield row[0], row.tolist()[1:]
        elif len(row) == 4:
            yield row[0], row.tolist()[1:] + (None,)
        else:
            raise IndexError("Input parameters are not length 4 or 5")


def read_parameter_dict(obj):
    for name, values in obj.items():
        output = []
        for key in _EXTERNAL_PARAMETER_CATEGORIES:
            output.append(values[key])
        for key in _OPTIONAL_PARAMETER_CATEGORIES:
            output.append(values.get(key, None))
        yield name, output


PARAMETER_READERS = {
    ndarray: read_parameter_array,
    dict: read_parameter_dict,
    PKDict: read_parameter_dict
}

# TODO: Pydantic parameter models either need to go in Parameters.parameters
#       or I need to just refactor the access to parameters. The latter could make for better handling
#       of new options like 'scale'

class Parameters:
    def __init__(self):
        self.parameters = {}
        self._NAMES = []
        self._LOWER_BOUND = 'lb'
        self._UPPER_BOUND = 'ub'
        self._START = 'start'
        self._SAMPLES = 'samples'
        self.fields = (self._LOWER_BOUND, self._UPPER_BOUND, self._START, self._SAMPLES)

    def parse(self, name, values):
        if name in self._NAMES:
            raise KeyError(f'Parameter {name} is defined multiple times')
        _validate_parameter(name, *values[:3])
        self._NAMES.append(name)
        self.parameters[name] = {}
        for field, value in zip(self.fields, values):
            self.parameters[name][field] = value

    def get_parameter_names(self):
        return self._NAMES

    def get_lower_bound(self):
        return np.array([self.parameters[name][self._LOWER_BOUND] for name in self._NAMES])

    def get_upper_bound(self):
        return np.array([self.parameters[name][self._UPPER_BOUND] for name in self._NAMES])

    def get_start(self):
        return np.array([self.parameters[name][self._START] for name in self._NAMES])

    def get_samples(self):
        samples = [self.parameters[name][self._SAMPLES] for name in self._NAMES]

        # Because samples is not required there are no prior validations
        vals = set(samples)
        if len(vals) == 1 and None in vals:
            # samples were not set for any parameters
            return samples
        elif None in vals:
            # samples were set for some parameters and not others
            assert ValueError("Not all parameters had samples field set")
        else:
            # samples were properly set for all parameters
            return samples