import typer
from typing_extensions import Annotated
from pathlib import Path
from rsopt.pkcli.logparser import print_failed_log

app = typer.Typer(invoke_without_command=True)

@app.command()
def failed(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to the rsopt YAML config file. If not given, searches for a .yml file in the current directory.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    log_file: Annotated[
        Path,
        typer.Option(
            "--log-file",
            "-l",
            help="Path to the libE_stats.txt log file. Defaults to 'libE_stats.txt'.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    run: Annotated[
        int,
        typer.Option(
            "--run",
            "-r",
            help="The run number to inspect (1-based). Defaults to the last run.",
            min=1,  # Run number must be positive
        ),
    ] = None,
):
    """
    Finds and prints the error logs for the first failed simulation in a given run.
    """
    # The functions expect string paths or None, so we convert the Path objects.
    config_path_str = str(config) if config else None
    log_file_path_str = str(log_file) if log_file else None

    print_failed_log(
        config_path=config_path_str,
        libe_stats_path=log_file_path_str,
        run_number=run
    )


@app.callback()
def main(
    ctx: typer.Context,
    # The callback needs to accept all the arguments that the default command might need
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to the rsopt YAML config file. If not given, searches for a .yml file in the current directory.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    log_file: Annotated[
        Path,
        typer.Option(
            "--log-file",
            "-l",
            help="Path to the libE_stats.txt log file. Defaults to 'libE_stats.txt'.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    run: Annotated[
        int,
        typer.Option(
            "--run",
            "-r",
            help="The run number to inspect (1-based). Defaults to the last run.",
            min=1,
        ),
    ] = None,
):
    """
    CLI for inspecting rsopt logs. By default, it runs the 'failed' command.
    """
    # If no subcommand was explicitly called, we invoke the 'failed' command
    if ctx.invoked_subcommand is None:
        ctx.invoke(failed, config=config, log_file=log_file, run=run)


if __name__ == "__main__":
    app()

