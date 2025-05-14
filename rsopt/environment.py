import jinja2
import pathlib
import rsopt.util
import shutil

_ENV_TEMPLATE = 'env_setup.jinja'
ENV_RUN_FILE = 'env_setup'
_TEMPLATE_PATH = rsopt.util.package_data_path()


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


def _get_application_path(application_name: str) -> str:
    # Check if applications exists in the run directory
    full_path = shutil.which(pathlib.Path('.').joinpath(application_name).absolute())
    # shutil.which will check in PATH and also passes if the full path to an executable was given
    if not full_path:
        full_path = shutil.which(application_name)

    assert full_path, f"Could not find a path for application: {application_name}"
    return str(full_path)


def get_run_command_with_path(job: "import rsopt.configuration.schemas.code") -> str:
    from rsopt.libe_tools.executors import EXECUTION_TYPES
    if job.setup.execution_type == EXECUTION_TYPES.SHIFTER:
        run_command = 'shifter'
        return _get_application_path(run_command)

    return _get_application_path(job.run_command)
