import abc
import pydantic
import typing
# TODO: This will completely replace the rsopt.configuration.options.Options
#       Options schema will also be removed

class Options(pydantic.BaseModel, abc.ABC):
    # TODO: software can probably be an enum and will be a discriminator
    software: str
    nworkers: int = 2
    run_dir: str = './ensemble/'
    record_interval: int = 1
    use_worker_dirs: bool = True
    sim_dirs_make: bool = True
    output_file: str = ''
    copy_final_logs: bool = True
    sym_links: list[typing.Union[pydantic.FilePath, pydantic.DirectoryPath]] = pydantic.Field(default_factory=list)
    objective_function: tuple[pydantic.FilePath, str]
    seed: typing.Union[None, str, int] = ''

    # TODO: This could end up being its own model
    executor_options: dict = pydantic.Field(default_factory=dict)

    use_zero_resources: bool = pydantic.Field(default=True, frozen=True)

    @property
    @abc.abstractmethod
    def type(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def methods(self) -> list[str]:
        pass

    # def get_sim_specs(self):
    #     # This is the most common sim_spec setting. It is updated by libEnsembleOptimizer if a different value needed.
    #     # TODO: It's not clear why this is defined here.
    #     #  It is something that will vary by Option class but is otherwise static.
    #     #  Maybe it should be put into the options schema?
    #     sim_specs = {
    #         'in': ['x'],
    #         'out': [('f', float), ]
    #     }
    #
    #     return sim_specs

class SimSpecs(pydantic.BaseModel):
    inputs: list[str] = pydantic.Field(alias='in')
    outputs: list[str]

class Method(pydantic.BaseModel):
    method: str
    se
    aposmm_support: bool
    local_support: bool
    persis_in: list[str]
    sim_specs: SimSpecs


class ExitCriteria(pydantic.BaseModel):
    sim_max: typing.Optional[int]
    gen_max: typing.Optional[int]
    elapsed_wallclock_time: typing.Optional[float]
    stop_val: typing.Optional[tuple[str, float]]

class OptionsExit(Options):
    exit_criteria: ExitCriteria

    """
  software_options:
    typing:
      - dict
  method:
    typing:
      - str
    """

