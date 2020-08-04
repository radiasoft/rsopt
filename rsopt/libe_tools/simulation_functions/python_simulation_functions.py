import numpy as np
from libensemble.message_numbers import WORKER_DONE, WORKER_KILL, TASK_FAILED

# TODO: This should probably derive from a base simulation_function class


def get_x_from_H(H):
    x = H['x'][0]
    return x


def _merge_dicts(base, derived, depth=-1):
    """Copy the items in the base dictionary into the derived dictionary, to the specified depth
    from: https://github.com/radiasoft/sirepo/blob/master/sirepo/simulation_db.py
    Args:
        base (dict): source
        derived (dict): receiver
        depth (int): how deep to recurse:
            >= 0:  <depth> levels
            < 0:   all the way
    """
    if depth == 0:
        return
    for key in base:
        # Items with the same name are not replaced
        if key not in derived:
            derived[key] = base[key]
        else:
            try:
                derived[key].extend(x for x in base[key] if x not in derived[key])
            except AttributeError:
                # The value was not an array
                pass
        try:
            _merge_dicts(base[key], derived[key], depth - 1 if depth > 0 else depth)
        except TypeError:
            # The value in question is not itself a dict, move on
            pass


def get_signature(parameters, settings):
    # No lambda functions are allowed in settings and parameter names may not be referenced
    # Just needs to insert parameter keys into the settings dict, but they won't have usable values yet

    signature = settings.settings.copy()

    for key in parameters._NAMES:
        signature[key] = None

    return signature


class PythonFunction:

    def __init__(self, function, parameters, settings):
        self.function = function
        self.parameters = parameters
        self.settings = settings
        self.signature = get_signature(parameters, settings)
        self.x_struct = {}

        # Received from libEnsemble during function evaluation
        self.H = None
        self.persis_info = None
        self.sim_specs = None
        self.libE_info = None

    def __call__(self, H, persis_info, sim_specs, libE_info):

        self.H = H
        self.persis_info = persis_info
        self.sim_specs = sim_specs
        self.libE_info = libE_info

        # Set function argument inputs
        x = get_x_from_H(H)
        self.parse_x(x)
        _, kwargs = self.compose_args(x, self.signature)

        # Function call and handling
        f = self.call_function(kwargs)
        output = self.format_evaluation(f)

        # FUTURE: Error handling for function call?
        return output, persis_info, WORKER_DONE

    def parse_x(self, x):
        self.x_struct = {}
        for val, name in zip(x, self.parameters._NAMES):
            self.x_struct[name] = val

    def compose_args(self, x, signature):
        return None, None

    def call_function(self, kwargs):
        f = self.function(**kwargs)

        return f

    def format_evaluation(self, container):
        if not hasattr(container, '__iter__'):
            container = (container,)
        # FUTURE: Type check for container values against spec
        outspecs = self.sim_specs['out']
        output = np.zeros(1, dtype=outspecs)
        for spec, value in zip(outspecs, container):
            output[spec] = value

        return output
