import pydantic
import pytest
from rsopt import parse


BASE_CONFIG = {
    'codes':
        [
            {'python':
                 {'parameters':
                      {
                          'a': {'min': 5, 'max': 10, 'start': 8, 'samples': 9, 'group': 1},
                          'b': {'min': 5, 'max': 10, 'start': 8, 'samples': 9, 'group': 1},
                          'c': {'min': 5, 'max': 10, 'start': 8, 'samples': 19, 'group': 'bears'},
                          'd': {'min': 5, 'max': 10, 'start': 8, 'samples': 19, 'group': 'bears'},
                          'e': {'min': 5, 'max': 10, 'start': 8, 'samples': 12, },
                       },
                  'setup':
                      {'execution_type': 'serial',
                       'input_file': 'test_configuration_validators.py',
                       'function': '_foo'}
                  }
             }
        ],
    'options':
        {'software': 'mesh_scan'}
}


def _foo():
    pass


@pytest.mark.parametrize('samples', (1, ))
def test_parameter_groups_raise_exception(samples):
    with pytest.raises(pydantic.ValidationError):
        config = BASE_CONFIG.copy()
        config['codes'][0]['python']['parameters']['a']['samples'] = samples
        parse.parse_sample_configuration(config)


def test_parameter_groups_pass():
    parse.parse_sample_configuration(BASE_CONFIG)
