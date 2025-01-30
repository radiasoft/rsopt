import jinja2
import pathlib

_ENV_TEMPLATE = 'env_setup.jinja'
ENV_RUN_FILE = 'env_setup'

# TODO: This needs to be set to use importlib resources
_TEMPLATE_PATH = '.'  #pkio.py_path(pkresource.filename(''))

def generate_env_setup(environment_variables) -> str:
    if environment_variables:
        template_loader = jinja2.FileSystemLoader(searchpath=_TEMPLATE_PATH)
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template(_ENV_TEMPLATE)

        output_template = template.render(dict_item=environment_variables)

        with open(pathlib.Path('.').joinpath(ENV_RUN_FILE), 'w') as f:
            f.write(output_template)

        return ENV_RUN_FILE

    return ''