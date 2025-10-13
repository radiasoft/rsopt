import numpy as np
import pathlib
import pandas as pd
import pydantic
from ruamel.yaml import YAML
import sortedcontainers
import typing

_SIM_PATH_ZEROS = 4

class BaseResult(pydantic.BaseModel, extra='allow'):
    sim_id: int = pydantic.Field(frozen=True)
    sim_worker: int = pydantic.Field(frozen=True)
    sim_ended: bool = pydantic.Field(frozen=True)
    sim_started: bool = pydantic.Field(frozen=True)
    f: float = pydantic.Field(frozen=True)
    fvec: list[float] = pydantic.Field(None, frozen=True)
    base_path: pathlib.Path = pydantic.Field(frozen=True)

    @property
    def path(self) -> pathlib.Path:
        return self.base_path.joinpath(f"worker{self.sim_worker}/sim{self.sim_id:0{_SIM_PATH_ZEROS}}")
    
    # Override the representation methods to prevent extremely long outputs from user-defined attributes
    def __repr__(self):
        fields = ", ".join(f"{k}={repr(v)}" for k, v in self.model_dump().items() if k not in self.model_extra.keys())
        return f"{self.__class__.__name__}({fields})"
    
    def __str__(self):
        fields = " ".join(f"{k}={repr(v)}" for k, v in self.model_dump().items() if k not in self.model_extra.keys())
        return f"{fields}"
    
# TODO: Have Results define arrays of values for all stored results?
class Results:
    def __init__(self, results, parameters):
        # Create an index for each attribute
        self._indexed_parameters = {param: sortedcontainers.SortedDict() for param in parameters + ['f']}
        self._results = np.array(results)
        self._mask = np.array([r.sim_ended for r in results])
        self.results = self._results[self._mask]

        # Populate the indexes
        for obj in results:
            for param in parameters + ['f']:
                value = getattr(obj, param)
                if value not in self._indexed_parameters[param]:
                    self._indexed_parameters[param][value] = []
                self._indexed_parameters[param][value].append(obj)
                
    def __iter__(self):
        return iter(self.results)
    
    def __len__(self):
        return len(self.results)

    def __getitem__(self, index):
        return self.results[index]
    
    def gather(self, quantity: str) -> np.ndarray:
        """Gather values from all results.
        
        quantity: (str) Quantity to gather. May be a parameter, setting, or libEnsemble history datum.
        
        returns arrays of values.
        """
        values = [getattr(q, quantity) for q in self.results]
        
        return np.array(values)

    def range_query(self, parameter: str, low, high):
        index = self._indexed_parameters[parameter]
        keys_in_range = index.irange(low, high)
        result = []
        for key in keys_in_range:
            result.extend(index[key])
        return result


def history_to_dict(H: np.ndarray, x_names=None) -> dict:
    data = {}
    for name in H.dtype.names:
        if name == 'x':
            for i, row in enumerate(H[name].T):
                rn = x_names[i] if x_names is not None else f'x{i}'
                data[rn] = row
            continue
        data[name] = H[name]

    return data

def gather_config_params(config: dict) -> list[str]:
    parameters = []
    for code in config['codes']:
        code_type = [k for k in code.keys()][0]  # should be len==1
        if not code[code_type].get('parameters'):
            continue
        parameters.extend(code[code_type].get('parameters').keys())

    return parameters

def create_model(config: dict) -> pydantic.BaseModel:
    x_keys = gather_config_params(config)
    Result = pydantic.create_model(
        'Result',
                    **{x: (typing.Union[float, str, int], ...) for x in x_keys},
                    __base__=BaseResult
    )

    return Result


def load_results(directory: str,
                 config_name: str or None = None,
                 history_name: str or None = None) -> Results:
    directory = pathlib.Path(directory)
    config = YAML(typ='safe').load(
        pathlib.Path(config_name) if config_name is not None else [f for f in directory.glob('*.yml')][0]
    )
    history = np.load(history_name if history_name is not None else [f for f in directory.glob('*.npy')][0], allow_pickle=True)

    x_names = gather_config_params(config)
    model = create_model(config)
    
    results = []
    
    for h in history:
        results.append(
            model(**history_to_dict(h, x_names=x_names), base_path=directory)
        )
        
    return Results(results, gather_config_params(config))



