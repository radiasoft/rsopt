import copy
import pathlib
import numpy as np
import pydantic
import pytest
from rsopt import parse
from rsopt.codes import python
from rsopt.configuration.options import SUPPORTED_OPTIONS
from rsopt.configuration.schemas import configuration, parameters, settings

SUPPORT_PATH = pathlib.Path(__file__).parent / 'support'
CONFIG_FILE = SUPPORT_PATH / 'config_six_hump_camel.yaml'

PARAMETERS = {
    'period': {'min': 30., 'max': 60., 'start': 46.},
    'lpy': {'min': 1., 'max': 10., 'start': 5.},
    'lmz': {'min': 10., 'max': 40., 'start': 20.},
    'lpz': {'min': 30., 'max': 60., 'start': 35.},
    'offset': {'min': .25, 'max': 4., 'start': 1.},
}

SETTINGS = {
    'lpx': 65,
    'pole_properties': 'h5',
    'pole_segmentation': [2, 2, 5],
    'pole_color': [1, 0, 1],
    'lmx': 65,
    'magnet_properties': 'sdds',
    'magnet_segmentation': [1, 3, 1],
    'magnet_color': [0, 1, 1],
    'gap': 20.,
}

EXIT_CRITERIA = {'sim_max': 10}

# Smallest options block each supported software accepts
MINIMAL_OPTIONS = {
    'mesh_scan': {},
    'lh_scan': {'software_options': {'batch_size': 512}},
    'dfols': {'software_options': {'components': 128}, 'exit_criteria': EXIT_CRITERIA},
    'dlib': {'exit_criteria': EXIT_CRITERIA},
    'pysot': {'exit_criteria': EXIT_CRITERIA},
    'nsga2': {'software_options': {'pop_size': 20, 'n_objectives': 2}, 'exit_criteria': EXIT_CRITERIA},
    'scipy': {'method': 'Nelder-Mead', 'exit_criteria': EXIT_CRITERIA},
    'nlopt': {'method': 'LN_SBPLX', 'exit_criteria': EXIT_CRITERIA},
    'mobo': {'software_options': {'reference_point': {'f1': 2000., 'f2': 2000.}, 'num_of_objectives': 2},
             'exit_criteria': EXIT_CRITERIA},
    'aposmm': {'method': 'LN_BOBYQA', 'software_options': {'initial_sample_size': 42},
               'exit_criteria': EXIT_CRITERIA},
    'pybobyqa': {'exit_criteria': EXIT_CRITERIA},
}


def _config(parameters=None, settings=None, software='mesh_scan', **setup):
    python_job = {
        'setup': {
            'input_file': str(SUPPORT_PATH / 'six_hump_camel.py'),
            'function': 'six_hump_camel_func',
            'execution_type': 'serial',
            **setup,
        },
    }
    if parameters is not None:
        python_job['parameters'] = copy.deepcopy(parameters)
    if settings is not None:
        python_job['settings'] = copy.deepcopy(settings)

    return {
        'codes': [{'python': python_job}],
        'options': {'software': software, **copy.deepcopy(MINIMAL_OPTIONS[software])},
    }


def _job(**kwargs):
    return parse.parse_sample_configuration(_config(**kwargs)).codes[0]


# Parameters

def test_numeric_parameters_read():
    job = _job(parameters=PARAMETERS)

    assert [p.name for p in job.parameters] == list(PARAMETERS)
    for param in job.parameters:
        assert isinstance(param, parameters.NumericParameter)
        assert (param.min, param.max, param.start) == tuple(PARAMETERS[param.name].values())
        assert param.samples == 1
        assert param.scale == 'linear'
        assert param.group is None


def test_parameters_set_as_attributes():
    job = _job(parameters=PARAMETERS)

    for param in job.parameters:
        assert getattr(job, param.name) is param


def test_category_parameter_read():
    job = _job(parameters={'mode': {'values': ['a', 'b', 'c']}})
    param = job.parameters[0]

    assert isinstance(param, parameters.CategoryParameter)
    assert param.samples == 3
    assert param.start == 'a'


def test_repeated_parameter_read():
    job = _job(parameters={'v': {'min': -1., 'max': 1., 'start': 0., 'dimension': 3}})
    param = job.parameters[0]

    assert isinstance(param, parameters.RepeatedNumericParameter)
    np.testing.assert_array_equal(param.min, [-1., -1., -1.])
    np.testing.assert_array_equal(param.max, [1., 1., 1.])
    np.testing.assert_array_equal(param.start, [0., 0., 0.])


def test_unknown_parameter_field_rejected():
    with pytest.raises(pydantic.ValidationError):
        _job(parameters={'a': {'min': 0., 'max': 1., 'start': 0., 'not_a_field': 1}})


def test_no_parameters():
    assert _job().parameters == []


# Settings

def test_settings_read():
    job = _job(settings=SETTINGS)

    assert [(s.name, s.value) for s in job.settings] == list(SETTINGS.items())
    for setting in job.settings:
        assert isinstance(setting, settings.Setting)
        assert getattr(job, setting.name) is setting


def test_name_in_parameters_and_settings_rejected():
    # Raised directly from a model validator; pydantic does not wrap NameError in a ValidationError
    with pytest.raises(NameError, match='already defined in settings'):
        _job(parameters={'gap': {'min': 0., 'max': 1., 'start': 0.}}, settings=SETTINGS)


def test_get_kwargs():
    job = _job(parameters=PARAMETERS, settings=SETTINGS)
    x = [1., 2., 3., 4., 5., 6., 7.]

    args, kwargs = job.get_kwargs(x, start_index=2)

    assert args == x[2:]
    assert kwargs == {**dict(zip(PARAMETERS, x[2:])), **SETTINGS}


# Options

def test_minimal_options_cover_supported_options():
    assert set(MINIMAL_OPTIONS) == set(SUPPORTED_OPTIONS.__members__)


def test_sample_and_optimize_names_partition_supported_options():
    sample_names = set(SUPPORTED_OPTIONS.get_sample_names())
    optimize_names = set(SUPPORTED_OPTIONS.get_optimize_names())

    assert sample_names == {'mesh_scan', 'lh_scan'}
    assert sample_names.isdisjoint(optimize_names)
    assert sample_names | optimize_names == set(SUPPORTED_OPTIONS.__members__)


@pytest.mark.parametrize('option', SUPPORTED_OPTIONS, ids=lambda o: o.name)
def test_options_set(option):
    options = option.model.model_validate({'software': option.name, **MINIMAL_OPTIONS[option.name]})

    assert isinstance(options, option.model)
    assert options.software == option.name


@pytest.mark.parametrize('option', [o for o in SUPPORTED_OPTIONS if MINIMAL_OPTIONS[o.name]], ids=lambda o: o.name)
def test_missing_required_options(option):
    with pytest.raises(pydantic.ValidationError) as exc_info:
        option.model.model_validate({'software': option.name})

    missing = {e['loc'][0] for e in exc_info.value.errors() if e['type'] == 'missing'}
    assert missing == set(MINIMAL_OPTIONS[option.name])


def test_software_options_validated_against_method():
    with pytest.raises(pydantic.ValidationError):
        SUPPORTED_OPTIONS.nlopt.model.model_validate(
            {'software': 'nlopt', 'method': 'LN_SBPLX', 'exit_criteria': EXIT_CRITERIA,
             'software_options': {'not_an_nlopt_option': 1}}
        )


# Configuration

@pytest.mark.parametrize('software', SUPPORTED_OPTIONS.get_sample_names())
def test_parse_sample_configuration(software):
    config = parse.parse_sample_configuration(_config(PARAMETERS, software=software))

    assert isinstance(config, configuration.ConfigurationSample)
    assert config.options.software == software


@pytest.mark.parametrize('software', SUPPORTED_OPTIONS.get_optimize_names())
def test_parse_optimize_configuration(software):
    config = parse.parse_optimize_configuration(_config(PARAMETERS, software=software))

    assert isinstance(config, configuration.ConfigurationOptimize)
    assert config.options.software == software


def test_sample_configuration_rejects_optimizer():
    with pytest.raises(pydantic.ValidationError):
        parse.parse_sample_configuration(_config(PARAMETERS, software='nlopt'))


def test_optimize_configuration_rejects_sampler():
    with pytest.raises(pydantic.ValidationError):
        parse.parse_optimize_configuration(_config(PARAMETERS, software='mesh_scan'))


@pytest.mark.parametrize('software, expected', [
    ('mesh_scan', configuration.ConfigurationSample),
    ('nlopt', configuration.ConfigurationOptimize),
])
def test_parse_unknown_configuration(software, expected):
    config = parse.parse_unknown_configuration(_config(PARAMETERS, software=software))

    assert type(config) is expected


@pytest.mark.parametrize('setup', [
    {'force_executor': True},
    {'execution_type': 'parallel', 'cores': 2},
], ids=['force_executor', 'mpi'])
def test_objective_function_required_without_worker_python(setup):
    # A Python job run through an Executor cannot hand its result back, so an objective function is needed
    with pytest.raises(pydantic.ValidationError, match='objective_function'):
        parse.parse_optimize_configuration(_config(PARAMETERS, software='nlopt', **setup))


def test_objective_function_satisfies_requirement():
    config = _config(PARAMETERS, software='nlopt', force_executor=True)
    config['options']['objective_function'] = [str(SUPPORT_PATH / 'six_hump_camel.py'), 'six_hump_camel_func']

    config = parse.parse_optimize_configuration(config)

    assert config.options.instantiated_objective_function(0., 0.) == 0.


def test_unknown_top_level_key_rejected():
    config = _config(PARAMETERS)
    config['not_a_key'] = {}

    with pytest.raises(pydantic.ValidationError):
        parse.parse_sample_configuration(config)


def test_flattened_parameter_vectors():
    params = {**PARAMETERS, 'v': {'min': -1., 'max': 1., 'start': 0., 'dimension': 2}}
    config = parse.parse_optimize_configuration(_config(params, software='nlopt'))

    np.testing.assert_array_equal(config.lower_bounds, [p['min'] for p in PARAMETERS.values()] + [-1., -1.])
    np.testing.assert_array_equal(config.upper_bounds, [p['max'] for p in PARAMETERS.values()] + [1., 1.])
    np.testing.assert_array_equal(config.start, [p['start'] for p in PARAMETERS.values()] + [0., 0.])
    assert config.dimension == len(PARAMETERS) + 2


# YAML

def test_config_read():
    config_dict = parse.read_configuration_file(CONFIG_FILE)

    assert set(config_dict) == {'codes', 'options'}
    assert list(config_dict['codes'][0]) == ['python']
    assert config_dict['options']['software'] == 'nlopt'


def test_config_import(monkeypatch):
    # input_file in the YAML is relative to tests/
    monkeypatch.chdir(SUPPORT_PATH.parent)
    config = parse.parse_optimize_configuration(parse.read_configuration_file(CONFIG_FILE))

    assert config.options.software == 'nlopt'
    assert config.options.method.name == 'LN_BOBYQA'
    assert config.options.exit_criteria.sim_max == 30
    assert config.options.software_options.xtol_abs == 1e-6
    assert [p.name for p in config.codes[0].parameters] == ['x', 'y']


def test_job_setup(monkeypatch):
    monkeypatch.chdir(SUPPORT_PATH.parent)
    config = parse.parse_optimize_configuration(parse.read_configuration_file(CONFIG_FILE))
    python_job = config.codes[0]

    assert isinstance(python_job, python.Python)
    assert python_job.setup.input_file.is_file()
    assert not python_job.use_executor
    assert callable(python_job.get_function)
    assert python_job.get_function(x=0., y=0.) == 0.
