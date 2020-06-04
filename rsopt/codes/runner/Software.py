import numpy as np


def prepare_sbplx(schema):
    """
    Uses a YAML schema file to prepare parameters options for each code.
    Returns format appropriate for initializing the NLOPT SBPLX optimizer.

    :param schema:
    :return: min_vals (array): Min values for each parameter
             max_vals (array): Max values for each parameter
             start_vals (array): Start values for each parameter
    """
    min_vals, max_vals, start_vals = [], [], []
    for code in schema['codes']:
        for code_inputs in code.values():
            if code_inputs.get('parameters'):
                for parameter_settings in code_inputs['parameters']:
                    for key in parameter_settings:
                        min_vals.append(parameter_settings[key]['min'])
                        max_vals.append(parameter_settings[key]['max'])
                        start_vals.append(parameter_settings[key]['start'])

    return np.array(min_vals), np.array(max_vals), np.array(start_vals)


def process_sbplx(schema, parameters):
    parameter_names = []
    for code in schema['codes']:
        name = list(code.keys())[0]
        if code[name].get('parameters'):
            for param in code[name].get('parameters'):
                parameter_names.append(list(param.keys())[0])

    assert len(parameter_names) == len(parameters), "There are {} parameter names and {} parameters. " \
                                                    "Lengths must be equal.".format(len(parameter_names), len(parameters))

    parameter_dict = {}
    for name, val in zip(parameter_names, parameters):
        parameter_dict[name] = val

    return parameter_dict


optimization_software = {
    'nlopt_sbplx': {'input': prepare_sbplx,
                    'output': process_sbplx}
}