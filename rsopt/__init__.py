# -*- coding: utf-8 -*-
u""":mod:`rsopt` package

:copyright: Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import pkg_resources
from pykern import pkio
from pykern import pkresource


try:
    # We only have a version once the package is installed.
    __version__ = pkg_resources.get_distribution('rsopt').version
except pkg_resources.DistributionNotFound:
    pass

_EXAMPLE_SYMLINK = pkio.py_path(pkresource.filename('examples'))
_EXAMPLE_REGISTRY = pkio.py_path(pkresource.filename('example_registry.yml'))
_EXECUTOR_SCHEMA = pkio.py_path(pkresource.filename('executor_schema.yml'))
_OPTIMIZER_SCHEMA = pkio.py_path(pkresource.filename('optimizer_schema.yml'))
_SETUP_SCHEMA = pkio.py_path(pkresource.filename('setup_schema.yml'))
