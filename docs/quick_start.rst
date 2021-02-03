.. _start_ref:

Getting started with rsopt
==========================

To get started with rsopt you can try installing from pip from rsopt's GitHub repository with two commands.
The first to install Pykern, which is needed to run the rsopt installation, and then rsopt::

    pip install pykern
    pip install git+https://github.com/radiasoft/rsopt

For more more details on rsopt installation and instructions for NERSC see the :doc:`Installation</installation>`

Once rsopt is installed you can try it out by running in a terminal::

    rsopt quickstart start

This will create two files in the directory where it is run.

    - ``rsopt_example.yml``: An example configuration file, written in YAML, that can be used to run he same optimization
            problem.
    - ``rsopt_example.py``: An example Python file that will run a simple optimization problem
        through rsopt.

The canonical format for setting up an rsopt run is to write configuration files in YAML that are used
to setup and execute the job sequence. Setting up your rsopt job through a configuration file offers the full range
of capabiilties available in rsopt such as job chaining between accelerator codes, parallel execution, and sampling.
There is also a subset of capabilities available for running serial optimization jobs through a Python script setup or
through a Python Jupyter notebook.

