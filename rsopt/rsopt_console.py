# -*- coding: utf-8 -*-
u"""Front-end command line for :mod:`rsopt`.
:copyright: Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from rsopt import codes
import os
import typer
from rsopt.pkcli.sample import app as sample_app
from rsopt.pkcli.quickstart import app as quickstart_app
from rsopt.pkcli.pack import app as pack_app
from rsopt.pkcli.optimize import app as optimize_app
from rsopt.pkcli.cleanup import app as cleanup_app
app = typer.Typer()
app.add_typer(sample_app, name="sample")
app.add_typer(quickstart_app, name="quickstart")
app.add_typer(pack_app, name="pack")
app.add_typer(optimize_app, name="optimize")
app.add_typer(cleanup_app, name="cleanup")


def main():
    os.environ['SIREPO_FEATURE_CONFIG_SIM_TYPES'] = ':'.join(codes.SIREPO_SIM_TYPES)
    app()


if __name__ == '__main__':
    main()
