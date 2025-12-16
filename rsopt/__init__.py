""":mod:`rsopt` package

:copyright: Copyright (c) 2025 RadiaSoft LLC.  All Rights Reserved.
:license: https://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern import pkio
from pykern import pkresource
import importlib.metadata

try:
    # We only have a version once the package is installed.
    __version__ = importlib.metadata.version("rsopt")
except importlib.metadata.PackageNotFoundError:
    pass

EXAMPLE_SYMLINK = pkio.py_path(pkresource.filename("examples"))
EXAMPLE_REGISTRY = pkio.py_path(pkresource.filename("example_registry.yml"))
EXECUTOR_SCHEMA = pkio.py_path(pkresource.filename("executor_schema.yml"))
OPTIMIZER_SCHEMA = pkio.py_path(pkresource.filename("optimizer_schema.yml"))
SETUP_SCHEMA = pkio.py_path(pkresource.filename("setup_schema.yml"))
OPTIONS_SCHEMA = pkio.py_path(pkresource.filename("options_schema.yml"))
