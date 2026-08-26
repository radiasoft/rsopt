"""Tests for the Py-BOBYQA options model and the validation PybobyqaOptimizer applies to it.

Run from inside `tests/`: the configurations here reference `support/six_hump_camel.py`.
"""
import numpy as np
import pytest

from rsopt.parse import parse_optimize_configuration
from rsopt.libe_tools.optimizer_pybobyqa import PybobyqaOptimizer

pytest.importorskip('pybobyqa')


def build_config(software_options=None, nworkers=4, repeated=False):
    """An optimize configuration for the six-hump camel, dimension 2 unless `repeated` is set.

    With `repeated` the `x` parameter is three-dimensional, so the flattened parameter vector the
    optimizer works in has four entries while there are still only two named parameters.
    """
    x = {'min': -3., 'max': 3., 'start': 0.08}
    if repeated:
        x['dimension'] = 3

    return parse_optimize_configuration({
        'codes': [{'python': {
            'parameters': {'x': x,
                           'y': {'min': -2., 'max': 2., 'start': -0.7}},
            'setup': {'input_file': 'support/six_hump_camel.py',
                      'function': 'six_hump_camel_func',
                      'execution_type': 'serial'}}}],
        'options': {'software': 'pybobyqa',
                    'nworkers': nworkers,
                    'exit_criteria': {'sim_max': 30},
                    'software_options': software_options or {}}})


def configured_user_specs(**kwargs):
    optimizer = PybobyqaOptimizer(build_config(**kwargs))
    optimizer._configure_optimizer()
    return optimizer.gen_specs['user']


def test_default_is_no_additional_starts():
    user = configured_user_specs()

    assert user['additional_instance_starts'] == []


def test_valid_additional_starts_reach_the_generator():
    given = [[1.0, 0.5], [-2.5, 1.75]]
    user = configured_user_specs(software_options={'additional_instance_starts': given})

    assert np.array_equal(np.array(user['additional_instance_starts']), np.array(given))


def test_start_point_on_a_bound_is_accepted():
    """The bounds are inclusive, matching what Py-BOBYQA itself accepts."""
    user = configured_user_specs(software_options={'additional_instance_starts': [[-3.0, 2.0]]})

    assert np.array_equal(user['additional_instance_starts'][0], np.array([-3.0, 2.0]))


def test_wrong_dimension_is_rejected():
    with pytest.raises(ValueError) as excinfo:
        configured_user_specs(software_options={'additional_instance_starts': [[1.0, 0.5, 0.25]]})

    message = str(excinfo.value)
    assert 'entry 0' in message
    assert '3 value(s)' in message, 'the error must report the dimension the user supplied'
    assert 'dimension 2' in message, 'the error must report the dimension the problem has'


def test_dimension_is_the_flattened_vector_not_the_parameter_count():
    """A multi-dimensional parameter contributes more than one entry to a starting point."""
    with pytest.raises(ValueError, match='dimension 4'):
        configured_user_specs(repeated=True,
                              software_options={'additional_instance_starts': [[1.0, 0.5]]})

    user = configured_user_specs(repeated=True,
                                 software_options={'additional_instance_starts': [[1., 2., 3., 0.5]]})
    assert np.array_equal(user['additional_instance_starts'][0], np.array([1., 2., 3., 0.5]))


def test_out_of_bounds_start_is_rejected():
    with pytest.raises(ValueError) as excinfo:
        configured_user_specs(software_options={'additional_instance_starts': [[1.0, 0.5],
                                                                               [0.0, 7.0]]})

    message = str(excinfo.value)
    assert 'entry 1' in message
    assert '[1]' in message, 'the error must identify which index is out of bounds'
    assert '7.0' in message


def test_too_many_starts_for_an_explicit_instance_count():
    with pytest.raises(ValueError) as excinfo:
        configured_user_specs(software_options={'instances': 2,
                                                'additional_instance_starts': [[1.0, 0.5],
                                                                               [0.0, 1.0]]})

    message = str(excinfo.value)
    assert 'at most 1 may be given' in message
    assert '`instances` is set to 2' in message


def test_too_many_starts_for_the_default_instance_count():
    """With `instances` unset the limit comes from nworkers, which the error has to explain."""
    with pytest.raises(ValueError) as excinfo:
        configured_user_specs(nworkers=2,
                              software_options={'additional_instance_starts': [[1.0, 0.5]]})

    message = str(excinfo.value)
    assert 'at most 0 may be given' in message
    assert 'defaults to nworkers-1 = 1' in message


def test_non_numeric_start_is_rejected_by_the_model():
    with pytest.raises(ValueError, match='additional_instance_starts'):
        build_config(software_options={'additional_instance_starts': [['a', 'b']]})


def test_unknown_software_option_is_still_rejected():
    with pytest.raises(ValueError, match='extra_forbidden'):
        build_config(software_options={'additional_instance_start': [[1.0, 0.5]]})
