# TODO: Check local_opt setup for the key name to pass nlopt options to.
#  Set up separate libE class like with scipy
from rsopt.configuration.schemas import options
import pydantic
import typing

# Nlopt Generator setup only will pass a few specific arguments so we do not use "extra='allow'" for nlopt
class NloptOptionsBase(options.SoftwareOptions, extra='forbid'):
    xtol_rel: float = pydantic.Field(None, description='End optimization if relative tolerance level in function input (x) is reached.')
    xtol_abs: float = pydantic.Field(None, description='End optimization if absolute tolerance level in function input (x) is reached.')
    ftol_rel: float = pydantic.Field(None, description='End optimization if relative tolerance level in function output (f) is reached.')
    ftol_abs: float = pydantic.Field(None, description='End optimization if absolute tolerance level in function output (f) is reached.')

class NloptOptionsMma(NloptOptionsBase):
    grad_dimensions: int = pydantic.Field(..., description='Number of dimensions (size) of the gradient data.')

# Naming for nlopt algorithms should follow the NLopt usage
class MethodBobyqa(options.Method):
    name: typing.Literal['LN_BOBYQA'] = 'LN_BOBYQA'
    aposmm_support = True
    local_support = True
    persis_in = ['f', ]
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec: typing.ClassVar = NloptOptionsBase

class MethodCobyla(options.Method):
    name: typing.Literal['LN_COBYLA'] = 'LN_COBYLA'
    aposmm_support = True
    local_support = True
    persis_in = ['f', ]
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec: typing.ClassVar = NloptOptionsBase

class MethodNewuoa(options.Method):
    name: typing.Literal['LN_NEWUOA'] = 'LN_NEWUOA'
    aposmm_support = True
    local_support = True
    persis_in = ['f', ]
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec: typing.ClassVar = NloptOptionsBase

class MethodNelderMead(options.Method):
    name: typing.Literal['LN_NELDERMEAD'] = 'LN_NELDERMEAD'
    aposmm_support = True
    local_support = True
    persis_in = ['f', ]
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec: typing.ClassVar = NloptOptionsBase

class MethodSubplex(options.Method):
    name: typing.Literal['LN_SBPLX'] = 'LN_SBPLX'
    aposmm_support = True
    local_support = True
    persis_in = ['f', ]
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec: typing.ClassVar = NloptOptionsBase

class MethodMma(options.Method):
    name: typing.Literal['LD_MMA'] = 'LD_MMA'
    aposmm_support = True
    local_support = True
    persis_in = ['f', 'grad']
    sim_specs=options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={'grad_dimensions': ('grad', float)}
    )
    option_spec: typing.ClassVar = NloptOptionsMma
    _opt_return_code = [0]

_METHODS = typing.Union[MethodNelderMead, MethodCobyla, MethodBobyqa, MethodNewuoa, MethodSubplex, MethodMma]

class Nlopt(options.OptionsExit):
    software: typing.Literal['nlopt']
    method: _METHODS = pydantic.Field(..., discriminator='name')
    software_options: typing.Union[NloptOptionsBase, NloptOptionsMma] = NloptOptionsBase()
