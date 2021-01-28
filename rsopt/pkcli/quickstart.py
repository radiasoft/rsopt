import shutil
import os
from pykern import pkio
from pykern import pkresource
from pykern import pkyaml

_EXAMPLE_SYMLINK = pkio.py_path(pkresource.filename('examples'))
_EXAMPLE_REGISTRY = pkio.py_path(pkresource.filename('example_registry.yml'))


def _get_example_file_list(example_name):
    registry = pkyaml.load_file(_EXAMPLE_REGISTRY)
    return registry['examples'][example_name]


def start():
    my_name = 'start'
    example_file_list = _get_example_file_list(my_name)
    start_message = """
    Welcome to rsopt. 
    Examples files have been copied to your current directory. 
    To try using rsopt now you can run:

        rsopt optimize configuration rsopt_example.yml
    
    For a detailed overview of this example please see:
    https://rsopt.readthedocs.io/en/latest/quick_start
    """  # TODO: Make sure this link exists
    for filename in example_file_list:
        filepath = os.path.join(_EXAMPLE_SYMLINK, filename)
        shutil.copyfile(filepath, filename, follow_symlinks=True)

    print(start_message)