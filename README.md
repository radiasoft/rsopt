### rsopt

rsopt is a Python framework for testing and running black box optimization problems. It is intended to provide a 
high degree of modularity in user choice of optimization algorithms and code execution methods. 
This allows for users to easily move their code execution between computational 
environments and utilize algorithms from multiple libraries without having to refactor their own code.

rsopt utilizes Sirepo to provide templating for a number of codes related to particle accelerator simulation. 
This makes it easy to take existing input files and use them without any additional modification. 
Direct execution of Python code and arbitrary executables are also supported. 

For more information see the: http://rsopt.readthedocs.org/en/latest/

### Quick Installation Instructions

rsopt uses the Python package Pykern to handle installation. You can install Pykern with pip using:
```bash
pip install pykern
```
Then to install rsopt:
```bash
pip install git+https://github.com/radiasoft/rsopt
```

For more installation instruction, including on NERSC see the full documentation at:
https://rsopt.readthedocs.io/en/latest/installation.html

### Getting Started
In addition to the documentation there are a number of basic examples in the examples directory of this respository.

Or, if you installed using he above Quick Installation instructions you can also try out a simple
example by running:
```bash
rsopt quickstart start
```

This will create two files needed to run one of the examples and provide instructions on how to use them.


#### License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2020 RadiaSoft LLC.  All Rights Reserved.
