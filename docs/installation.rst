.. _installation_ref:

Installation
============

You will always need to ensure that the Python package pykern is installed prior to installing rsopt.
If pykern is not yet installed it can be added with pip by running::

    pip install pykern

For the minimum running configuration of rsopt you can install in a single command with::

    pip install git+https://github.com/radiasoft/rsopt

If you want to try examples bundled with rsopt you can download the repository from GitHub::

    git clone https://github.com/radiasoft/rsopt
    cd rsopt
    pip install .

To use rsopt with expanded support for particle tracking codes through Sirepo you will need to install with
the 'full' flag::

    git clone https://github.com/radiasoft/rsopt
    cd rsopt
    pip install .[full]




On NERSC
--------

Pykern is used in the install process and must be installed prior::

    pip install pykern --user

If you are using tracking codes (elegant, OPAL, etc.) you will need to install Sirepo separately::

    pip install git+https://github.com/radiasoft/sirepo --no-deps --user


Finally to install rsopt::

    git clone https://github.com/radiasoft/rsopt
    cd rsopt
    pip install .[nersc] --user


It is normal to see error messages stating Sirepo has dependencies which are not installed. These dependencies
are not needed for use of Sirepo by rsopt and intentionally left out during the NERSC installation process.
