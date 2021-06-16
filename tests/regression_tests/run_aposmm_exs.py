from rsopt.pkcli.optimize import configuration
import shutil

shutil.rmtree('../../examples/python_aposmm_example/ensemble', ignore_errors=True)
configuration('config_pysot.yaml')