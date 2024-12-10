import pathlib
from typing import Any
from ruamel.yaml import YAML
import numpy as np
import pandas as pd
import pydantic

_SIM_PATH_ZEROS = 4

class BaseResult(pydantic.BaseModel):
    sim_id: int
    sim_worker: int
    sim_ended: bool
    sim_started: bool
    base_path: pathlib.Path

    @property
    def path(self) -> pathlib.Path:
        return self.base_path.joinpath(f"worker{self.sim_worker}/sim{self.sim_id:0{_SIM_PATH_ZEROS}}")


class Results:
    def __init__(self, results, parameters):
        # Create an index for each attribute
        self._indexed_parameters = {param: sortedcontainers.SortedDict() for param in parameters}
        self.objects = results

        # Populate the indexes
        for obj in results:
            for param in parameters:
                value = getattr(obj, param)
                if value not in self._indexed_parameters[param]:
                    self._indexed_parameters[param][value] = []
                self._indexed_parameters[param][value].append(obj)

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
                    **{x: (float, ...) for x in x_keys},
                    __base__=BaseResult
    )

    return Result


def load_results(directory: str,
                 config_name: str or None = None,
                 history_name: str or None = None) -> pd.DataFrame:
    directory = pathlib.Path(directory)
    config = YAML(typ='safe').load(
        pathlib.Path(config_name) if config_name is not None else [f for f in directory.glob('*.yml')][0]
    )
    history = np.load(history_name if history_name is not None else [f for f in directory.glob('*.npy')][0])

    x_names = gather_config_params(config)
    model = create_model(config)

    results = []

    for h in history:
        results.append(
            model(**history_to_dict(h, x_names=x_names), base_path=directory)
        )

    return results






if __name__ == '__main__':
    test_H = '../examples/python_chwirut_example/H_run_scan_history_length-500_evals-500_workers-1.npy'
    H = np.load(test_H)

    test_config = pathlib.Path('../examples/python_chwirut_example/config_chwirut.yaml')
    config = YAML(typ='safe').load(test_config)

    res = gather_config_params(config)

    print(
        create_model(config)(
            **history_to_dict(H[0], x_names=res),
            base_path='ab'
        )
    )

