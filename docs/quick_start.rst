.. _start_ref:

Getting started with rsopt
==========================

Quick Installation
------------------
The fastest way to get started with rsopt is to use ``pip`` to run the installation in a terminal.
The first to install Pykern, which is needed to run the rsopt installation, and then rsopt::

    pip install pykern
    pip install git+https://github.com/radiasoft/rsopt

For more more details on rsopt installation and instructions for NERSC see the :doc:`Installation</installation>`

Quickstart
----------
Once rsopt is installed you can try it out by running in a terminal::

    rsopt quickstart start

This will create two files in the directory where it is run.

    - ``rsopt_example.yml``: An example configuration file, written in YAML, that can be used to run he same optimization
      problem.
    - ``rsopt_example.py``: Contains a Python function representing the function to be optimized.

To execute the example you can then run::

    rsopt optimize configuration rsopt_example.yml

The canonical format for setting up an rsopt run is to write configuration files in YAML that are used
to setup and execute the job sequence. Setting up your rsopt job through a configuration file offers the full range
of capabilities available in rsopt such as job chaining between accelerator codes, parallel execution, and sampling.
For information on setting up your own configuration files you can see the :doc:`Configuration</configuration>` documentation.
More examples can be found at: https://github.com/radiasoft/rsopt/tree/master/examples

