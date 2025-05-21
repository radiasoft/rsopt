# -*- coding: utf-8 -*-
u""":mod:`rsopt` package

:copyright: Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
import rsopt.util

__version__ = '0.1.0'


EXAMPLE_SYMLINK = rsopt.util.package_data_path() / 'examples'
EXAMPLE_REGISTRY = rsopt.util.package_data_path() / 'example_registry.yml'
EXECUTOR_SCHEMA = rsopt.util.package_data_path() / 'executor_schema.yml'
OPTIMIZER_SCHEMA = rsopt.util.package_data_path() / 'optimizer_schema.yml'
SETUP_SCHEMA = rsopt.util.package_data_path() / 'setup_schema.yml'
OPTIONS_SCHEMA = rsopt.util.package_data_path() / 'options_schema.yml'
