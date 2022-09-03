# -*- coding: utf-8 -*-
u""":mod:`rsopt` package

:copyright: Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import pkg_resources
import os

try:
    # We only have a version once the package is installed.
    __version__ = pkg_resources.get_distribution('rsopt').version
except pkg_resources.DistributionNotFound:
    pass

_PDATA_ROOT = os.path.abspath(os.path.dirname(__file__))
_MY_PDATA = os.path.join(_PDATA_ROOT, 'package_data')
_EXAMPLE_SYMLINK = os.path.join(_MY_PDATA, 'examples')
_EXAMPLE_REGISTRY = os.path.join(_MY_PDATA, 'example_registry.yml')
_EXECUTOR_SCHEMA = os.path.join(_MY_PDATA, 'executor_schema.yml')
_OPTIMIZER_SCHEMA = os.path.join(_MY_PDATA, 'optimizer_schema.yml')
_SETUP_SCHEMA = os.path.join(_MY_PDATA, 'setup_schema.yml')
_OPTIONS_SCHEMA = os.path.join(_MY_PDATA, 'options_schema.yml')
