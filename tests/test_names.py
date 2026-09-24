import pydantic
import pytest
from rsopt import parse
from rsopt.configuration.schemas.names import AttributeIndex, ItemAttributeIndex, RawName

_SPIFFE_INPUT = './support/spiffe/gun.spiffe'
_GENESIS_INPUT = './support/genesis/genesis_pegasus.in'
_PYTHON_INPUT = './support/six_hump_camel.py'


def _job(code, settings, input_file, **setup):
    config = {
        'codes': [{code: {'settings': settings, 'setup': {'input_file': input_file, 'execution_type': 'serial', **setup}}}],
        'options': {'software': 'mesh_scan'},
    }
    return parse.parse_sample_configuration(config).codes[0]


@pytest.mark.parametrize('name, expected', [
    ('Q1.K1', {'item': 'Q1', 'attribute': 'K1', 'index': None}),
    ('cmd.attr.2', {'item': 'cmd', 'attribute': 'attr', 'index': 2}),
])
def test_item_attribute_index(name, expected):
    assert ItemAttributeIndex.parse(name).model_dump(exclude={'raw'}) == expected


@pytest.mark.parametrize('name, expected', [
    ('gamma0', {'attribute': 'gamma0', 'index': None}),
    ('gamma0.2', {'attribute': 'gamma0', 'index': 2}),
])
def test_attribute_index(name, expected):
    assert AttributeIndex.parse(name).model_dump(exclude={'raw'}) == expected


@pytest.mark.parametrize('fmt, name', [
    (ItemAttributeIndex, 'Q1'),          # attribute required
    (ItemAttributeIndex, 'a.b.2.x'),     # too many parts
    (ItemAttributeIndex, 'a.b.c'),       # index not an integer
    (ItemAttributeIndex, 'a.b.0'),       # index is 1-based
    (AttributeIndex, 'a.b.c'),
])
def test_invalid_names(fmt, name):
    with pytest.raises(ValueError):
        fmt.parse(name)


def test_zero_based_index():
    assert ItemAttributeIndex.parse('cmd.attr.1').zero_based_index == 0
    assert ItemAttributeIndex.parse('cmd.attr').zero_based_index is None


def test_parsed_names_are_frozen():
    parsed_name = ItemAttributeIndex.parse('cmd.attr.1')
    with pytest.raises(pydantic.ValidationError):
        parsed_name.index = 2


def test_python_accepts_arbitrary_names():
    job = _job('python', {'model.solver.tol': 1e-6, 'a.b.c.d.e': 1}, _PYTHON_INPUT, function='six_hump_camel_func')
    assert job.parsed_name('model.solver.tol') == RawName(raw='model.solver.tol')
    assert job.get_kwargs([])[1] == {'model.solver.tol': 1e-6, 'a.b.c.d.e': 1}


def test_code_rejects_malformed_name_at_load():
    with pytest.raises(pydantic.ValidationError, match='must have between 2 and 3'):
        _job('spiffe', {'define_geometry': 1}, _SPIFFE_INPUT)


def test_unknown_parsed_name():
    job = _job('spiffe', {'define_geometry.nz': 515}, _SPIFFE_INPUT)
    with pytest.raises(NameError):
        job.parsed_name('define_geometry.zmin')


def test_spiffe_one_based_index(tmp_path):
    job = _job('spiffe', {'define_screen.z_position.2': 0.123}, _SPIFFE_INPUT)
    job.generate_input_file({'define_screen.z_position.2': 0.123}, str(tmp_path), is_parallel=False)

    written = (tmp_path / 'gun.spiffe').read_text()
    first, second = written.split('&define_screen')[1:3]
    assert '0.123' not in first
    assert '0.123' in second


def test_spiffe_repeated_command_requires_index(tmp_path):
    job = _job('spiffe', {'define_screen.z_position': 0.123}, _SPIFFE_INPUT)
    with pytest.raises(AssertionError, match='`command_index` must be set'):
        job.generate_input_file({'define_screen.z_position': 0.123}, str(tmp_path), is_parallel=False)


def test_genesis_attribute_name(tmp_path):
    # rsopt's genesis grammar only accepts double-quoted strings, the support file uses single quotes
    input_file = tmp_path / 'input' / 'genesis_pegasus.in'
    input_file.parent.mkdir()
    input_file.write_text(open(_GENESIS_INPUT).read().replace("'", '"'))
    job = _job('genesis', {'curpeak': 155.0}, str(input_file))
    assert job.parsed_name('curpeak') == AttributeIndex(raw='curpeak', attribute='curpeak')
    job.generate_input_file({'curpeak': 155.0}, str(tmp_path), is_parallel=False)
    assert '155.0' in (tmp_path / 'genesis_pegasus.in').read_text()
