from pykern.pkyaml import load_file
from rsopt.configuration import Configuration, Job
from rsopt.codes import _SUPPORTED_CODES

_CODE_FIELD = 'codes'  # TODO: Might be more consistent to change this this field title to 'jobs'
_PARAMETERS_FIELD = 'parameters'
_SETTINGS_FIELD = 'settings'
_SETUP_FIELD = 'setup'


def _DEFAULT_SETUP(code_name):
    # FUTURE: Could consider defining serial execution as a default
    raise KeyError(f'setup is not defined for {code_name}')


def _sanitize_fields(field: str):
    # apply allowed sanitization to configuration defined fields
    field = field.lower()

    return field


def _is_code_supported(code_name):
    # code can be run by rsopt
    return code_name in _SUPPORTED_CODES


def _read_codes_to_jobs(template: dict):
    # parse each code into a Job object
    job_list = []

    for code_name, code_dict in [code.popitem() for code in template[_CODE_FIELD]]:
        code_name = _sanitize_fields(code_name)
        assert _is_code_supported(code_name), f"{code_name} is not supported"

        new_job = Job(code_name)
        new_job.parameters = code_dict.get(_PARAMETERS_FIELD) or {}
        new_job.settings = code_dict.get(_SETTINGS_FIELD) or {}
        new_job.setup = code_dict.get(_SETUP_FIELD) or _DEFAULT_SETUP(code_name)

        job_list.append(new_job)

    return job_list


def read_configuration_file(filename):
    """
    Load a configuration file stored in YAML format into a dictionary
    :param filename: (str) Path to configuration file
    :return: (PKDict) Dictionary holding the configuration
    """
    return load_file(filename)


def parse_yaml_configuration(template: dict, configuration=None) -> Configuration:
    """
    Parse configuration into Configuration object
    :param template: (dict) Dictionary containing a configuration
    :return: (Configuration)
    """
    job_list = _read_codes_to_jobs(template)

    if not configuration:
        configuration = Configuration()
    configuration.set_jobs(job_list)

    return configuration
