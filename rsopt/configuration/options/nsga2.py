from rsopt.configuration.schemas import options
import pydantic
import typing


class Nsga2Options(pydantic.BaseModel, extra='forbid'):
    pop_size: int = pydantic.Field(..., description='Number of individuals in the population.')
    n_objectives: int = pydantic.Field(..., description="Number of objectives.")

    cxpb: float = pydantic.Field(0.8, description="Crossover probability.")
    eta: float = pydantic.Field(10.0, description="Scales the mutation rate.")
    # Default scaling of indpb is handled in EvolutionaryOptimizer since we need the problem dimensionality
    # which is checked by the Configuration object
    indpb: float = pydantic.Field(0.8, description="Probability that a gene changes. Default value will be "
                                                   "scaled by the individual dimension. If the user sets then "
                                                   "the exact value is used")


class MethodNsga2(options.Method):
    name: typing.Literal['pysot'] = 'nsga2'
    aposmm_support = False
    local_support = False
    persis_in = ['fitness_values', 'sim_id']
    sim_specs=options.SimSpecs(
        inputs=['individual'],
        static_outputs=[],
        dynamic_outputs={'n_objectives': ('fitness_values', float)},
    )
    option_spec = Nsga2Options


class Nsga2(options.OptionsExit):
    software: typing.Literal['nsga2'] = 'nsga2'
    method: typing.Union[MethodNsga2] = pydantic.Field(MethodNsga2(), discriminator='name')
    software_options: Nsga2Options
