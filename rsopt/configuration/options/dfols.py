from rsopt.configuration.schemas import options
import pydantic
import typing

_method_dfols = options.Method(
    name='dfols',
    aposmm_support=True,
    local_support=True,
    persis_in=['f', 'fvec'],
    sim_specs=options.SimSpecs(
        inputs=['x'],
        outputs=[['f', float], ['fvec', float, 'components']],
        # TODO: Add a dynamic outputs to explicitly mark data to set at run time?

    )
)


class Dfols(options.OptionsExit):
    software: typing.Literal['dfols']
    method = _method_dfols
    # TODO: Should everything like this just be moved under software_options?
    components: int
    @property
    def type(self) -> str:
        return 'local'

    @property
    def methods(self) -> list[str]:
        return ['dfols']

    _aposmm_sup