# -*- coding: utf-8 -*-
u"""rsopt setup script

:copyright: Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pksetup

pksetup.setup(
    name='rsopt',
    author='RadiaSoft LLC',
    author_email='pip@radiasoft.net',
    description='A Python library with tools for optimization problems',
    install_requires=[
        'pykern',
        'libEnsemble',
        'numpy'
    ],
    license='http://www.apache.org/licenses/LICENSE-2.0.html',
    url='https://github.com/radiasoft/rsopt',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
)
