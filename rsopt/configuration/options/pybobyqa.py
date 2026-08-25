from rsopt.configuration.schemas import options
import pydantic
import typing


class PybobyqaOptions(options.SoftwareOptions, extra='forbid'):
    seek_global_minimum: bool = pydantic.Field(True, description='Use Py-BOBYQA\'s multiple restart '
                                                                 'heuristic to seek a global minimum. Requires '
                                                                 'bounds on all parameters, which rsopt always '
                                                                 'provides. Py-BOBYQA\'s own default is False; '
                                                                 'rsopt defaults it on because the heuristic is '
                                                                 'the reason to prefer this implementation over '
                                                                 'the BOBYQA algorithm available from nlopt.')
    objfun_has_noise: bool = pydantic.Field(False, description='Tell Py-BOBYQA the objective is stochastic. '
                                                               'Changes several internal defaults, including '
                                                               'enabling restarts and using more interpolation '
                                                               'points.')
    npt: typing.Optional[pydantic.PositiveInt] = pydantic.Field(None, description='Number of interpolation points. '
                                                                                  'Must satisfy dim+1 <= npt <= '
                                                                                  '(dim+1)(dim+2)/2. Defaults to '
                                                                                  '2*dim+1 for a smooth objective.')
    rhobeg: typing.Optional[float] = pydantic.Field(None, description='Initial trust region radius.')
    rhoend: typing.Optional[float] = pydantic.Field(None, description='Trust region radius at which a run is '
                                                                      'considered converged. Defaults to 1e-8.')
    maxfun: typing.Optional[pydantic.PositiveInt] = pydantic.Field(None, description='Evaluation budget for a single '
                                                                                     'instance, counted across all of '
                                                                                     'that instance\'s internal '
                                                                                     'restarts. Not normally needed: '
                                                                                     'termination is governed by '
                                                                                     'exit_criteria, and an instance '
                                                                                     'that exhausts maxfun is '
                                                                                     'restarted from scratch, losing '
                                                                                     'the model it had built.')
    scaling_within_bounds: bool = pydantic.Field(True, description='Let Py-BOBYQA rescale parameters to the unit '
                                                                   'cube internally. Useful when parameter ranges '
                                                                   'differ by orders of magnitude.')
    user_params: dict = pydantic.Field(default_factory=dict, description='Advanced Py-BOBYQA settings passed through '
                                                                         'unchanged, e.g. '
                                                                         '{\'restarts.use_restarts\': True}. See the '
                                                                         'Py-BOBYQA documentation for the available '
                                                                         'keys. Validated by Py-BOBYQA, not by rsopt.')
    instances: typing.Optional[pydantic.PositiveInt] = pydantic.Field(None, description='Number of independent '
                                                                                        'Py-BOBYQA runs to keep going '
                                                                                        'at once. Defaults to '
                                                                                        'nworkers-1 so that every '
                                                                                        'simulation worker is kept '
                                                                                        'busy.')
    additional_instance_starts: list[list[float]] = pydantic.Field(default_factory=list,
        description='Explicit starting points for instances after the first. Instance 0 always '
                    'starts from the `start` values given for the parameters, so the points listed '
                    'here are used for instance 1 onwards, in order, and at most `instances`-1 of '
                    'them may be given. Any instance not covered starts from a random point within '
                    'the bounds, as do all relaunches after an instance converges. Each point is a '
                    'list in the flattened parameter vector space and must have one entry per '
                    'dimension of the problem, which is not the same as the number of named '
                    'parameters when any of them are multi-dimensional.')
    restart_on_convergence: bool = pydantic.Field(True, description='Start a new run from a new random point when an '
                                                                    'instance finishes, so its worker does not go '
                                                                    'idle. When False the run ends once every '
                                                                    'instance has finished.')


class MethodPybobyqa(options.Method):
    name: typing.Literal['pybobyqa'] = 'pybobyqa'
    aposmm_support = False
    local_support = False
    persis_in = ['f', 'sim_id']
    sim_specs = options.SimSpecs(
        inputs=['x'],
        static_outputs=[('f', float)],
        dynamic_outputs={}
    )
    option_spec = PybobyqaOptions


class Pybobyqa(options.OptionsExit):
    software: typing.Literal['pybobyqa'] = 'pybobyqa'
    method: typing.Union[MethodPybobyqa] = pydantic.Field(default=MethodPybobyqa(), discriminator='name')
    software_options: PybobyqaOptions = pydantic.Field(default=PybobyqaOptions())
