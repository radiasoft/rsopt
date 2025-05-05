import shutil
import os
from pykern import pkyaml
from ruamel.yaml import YAML
from rsopt import EXAMPLE_SYMLINK, EXAMPLE_REGISTRY
import typer

app = typer.Typer()


def _get_example_file_list(example_name):
    registry = YAML.load(EXAMPLE_REGISTRY)
    return registry['examples'][example_name]['files']


@app.command()
def start():
    """Generates files for the quickstart example in the current directory.

    See https://rsopt.readthedocs.io/en/latest/quick_start  for a detailed description  of the example.

    :return: None
    """
    my_name = 'start'
    example_file_list = _get_example_file_list(my_name)
    start_message = """
    Welcome to rsopt. 
    Examples files have been copied to your current directory. 
    To try using rsopt now you can run:

        rsopt optimize configuration rsopt_example.yml
    
    For a detailed overview of this example please see:
    https://rsopt.readthedocs.io/en/latest/quick_start
    """
    for filename in example_file_list:
        filepath = os.path.join(EXAMPLE_SYMLINK, filename)
        shutil.copyfile(filepath, filename, follow_symlinks=True)

    print(start_message)
