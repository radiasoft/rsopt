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
        'numpy',
        'nlopt',
        'mpmath',
        'jinja2>=3.0.1'
        'docutils==0.17'  # docutils>=0.18 may be breaking documentation build
    ],
    extras_require={
        'nersc': ['rsbeams@git+https://github.com/radiasoft/rsbeams',
                  'lume-genesis@git+https://github.com/cchall/lume-genesis',
                  # Inherited from sirepo
                  # sirepo binary build fails so it needs to be installed with --no-deps
                  'numconv',
                  'flask',
                  'user-agents',
                  'aenum',
                  'SQLAlchemy'
                  ],
        'full': [
            'rsbeams@git+https://github.com/radiasoft/rsbeams',
            'sirepo@git+https://github.com/radiasoft/sirepo',
            'lume-genesis@git+https://github.com/cchall/lume-genesis',
            'DFO-LS',  # If using dfols optimizer
            'pandas',  # Needed for some post-processing utilities
            'xopt',  # If using MOBO algorithm for optimization
            'pymoo'  # Used by some MOBO examples
        ]
    },
    license='http://www.apache.org/licenses/LICENSE-2.0.html',
    url='https://github.com/radiasoft/rsopt',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
)
