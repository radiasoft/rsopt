""":mod:`rsopt` package

:copyright: Copyright (c) 2025 RadiaSoft LLC.  All Rights Reserved.
:license: https://www.apache.org/licenses/LICENSE-2.0.html
"""
import importlib.metadata

try:
    # We only have a version once the package is installed.
    __version__ = importlib.metadata.version("rsopt")
except importlib.metadata.PackageNotFoundError:
    pass
