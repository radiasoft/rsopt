# Handle reading of YAML template files. Should just read in data and put it corresponding object.
# Will supplant some of the functionality held by Runner currently
# Configuration Parameter and Setting object will be defined externally
from pykern.pkyaml import load_file
from rsopt.configuration import Configuration, Job


# Templated codes have schema files that can be used to check input and create run files. Otherwise user
#   must supply module containing inputs
_TEMPLATED_CODES = ['elegant', ]

_CODE_FIELD = 'codes'  # TODO: Might be more consistent to change this this field title to 'jobs'
_PARAMETERS_FIELD = 'parameters'
_SETTINGS_FIELD = 'settings'
_SETUP_FIELD = 'setup'


def _DEFAULT_SETUP(code_name):
    # FUTURE: Could consider defining serial execution as a default
    raise KeyError(f'setup is not defined for {code_name}')


def read_configuration_file(filename):
    return load_file(filename)


def _sanitize_fields(field: str):
    field = field.lower()

    return field


def _is_code_supported(code_name):
    return code_name in _TEMPLATED_CODES


def _read_codes_to_jobs(template: dict):
    job_list = []

    for code_name, code_dict in template[_CODE_FIELD].popitem():
        code_name = _sanitize_fields(code_name)
        assert _is_code_supported(code_name), f"{code_name} is not supported"

        new_job = Job(code_name)
        new_job.set_parameters(code_dict.get(_PARAMETERS_FIELD) or {})
        new_job.set_settings(code_dict.get(_SETTINGS_FIELD) or {})
        new_job.set_setup(code_dict.get(_SETUP_FIELD) or _DEFAULT_SETUP(code_name))

        job_list.append(new_job)

    return job_list


def parse_yaml_template(template: dict) -> object:
    job_list = _read_codes_to_jobs(template)

    configuration = Configuration()
    configuration.set_jobs(job_list)

    return Configuration
