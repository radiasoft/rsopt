# -*- coding: utf-8 -*-
u"""Front-end command line for :mod:`rsopt`.

See :mod:`pykern.pkcli` for how this module is used.

:copyright: Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcli
import sys


def main():
    return pkcli.main('rsopt')


if __name__ == '__main__':
    sys.exit(main())
