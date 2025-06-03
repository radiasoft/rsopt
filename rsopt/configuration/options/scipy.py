from rsopt.configuration.schemas import options
import pydantic
import typing


class ScipyOptionsBase(options.SoftwareOptions, extra='allow'):
    pass
class ScipyOptionsBfgs(options.SoftwareOptions, extra='allow'):
    grad_dimensions: int = pydantic.Field(..., description='Number of dimensions (size) of the gradient data.')


# Naming for SciPy algorithms should follow the scipy.optimize usage
class MethodNelderMead(options.Method):
    name: typing.Literal['Nelder-Mead'] = 'Nelder-Mead'
    parent_software = 'scipy'
    aposmm_support = True
    local_support = True
    persis_in = ['f', ]
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec: typing.ClassVar = ScipyOptionsBase
    _opt_return_code = [0]

class MethodCobyla(options.Method):
    name: typing.Literal['COBYLA'] = 'COBYLA'
    parent_software = 'scipy'
    aposmm_support = True
    local_support = True
    persis_in = ['f', ]
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec: typing.ClassVar = ScipyOptionsBase
    _opt_return_code = [1]

class MethodBfgs(options.Method):
    name: typing.Literal['BFGS'] = 'BFGS'
    parent_software = 'scipy'
    aposmm_support = True
    local_support = True
    persis_in = ['f', 'grad']
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={'grad_dimensions': ('grad', float)}
    )
    option_spec: typing.ClassVar = ScipyOptionsBfgs
    _opt_return_code = [0]


_METHODS = typing.Union[MethodNelderMead, MethodCobyla, MethodBfgs]

class Scipy(options.OptionsExit):
    software: typing.Literal['scipy']
    method: _METHODS = pydantic.Field(..., discriminator='name')
    software_options: typing.Union[ScipyOptionsBase, ScipyOptionsBfgs] = ScipyOptionsBase()
