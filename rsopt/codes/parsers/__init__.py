import pickle
import typing
from rsopt import util


def parse_simulation_input_file(input_file: str, code_name, ignored_files: typing.List[str] or None = None,
                                shifter: bool = False) -> typing.Type['sirepo.lib.SimData'] or None:

    if shifter:
        # Must pass a list to ignored_files here since it is sent to subprocess
        d = _shifter_parse_model(code_name, input_file, ignored_files or [])
    else:
        import sirepo.lib
        d = sirepo.lib.Importer(code_name, ignored_files).parse_file(input_file)

    return d


def _shifter_parse_model(name: str, input_file: str, ignored_files: list) -> typing.Type['sirepo.lib.SimData'] or None:
    # Sidesteps the difficulty of Sirepo install on NERSC by running a script that parses to the Sirepo model
    import shlex
    from subprocess import Popen, PIPE

    _SHIFTER_BASH_FILE = util.package_data_path() / 'shifter_exec.sh'
    _SHIFTER_SIREPO_SCRIPT = util.package_data_path() / 'shifter_sirepo.py'
    _DEFAULT_SHIFTER_IMAGE = 'radiasoft/sirepo:prod'

    node_to_use = util.return_unused_node()
    if node_to_use:
        run_string = f"srun -w {node_to_use} --ntasks 1 --nodes 1 shifter --image={_DEFAULT_SHIFTER_IMAGE} " \
                     f"/bin/bash {_SHIFTER_BASH_FILE} python {_SHIFTER_SIREPO_SCRIPT}"
        run_string = ' '.join([run_string, name, input_file, *ignored_files])
        cmd = Popen(shlex.split(run_string), stderr=PIPE, stdout=PIPE)
        out, err = cmd.communicate()
        if err:
            print(err.decode())
            raise Exception('Model load from Sirepo in Shifter failed.')
        d = pickle.loads(out)
    else:
        d = None

    return util.broadcast(d)
