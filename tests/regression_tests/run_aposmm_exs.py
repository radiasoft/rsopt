from rsopt.pkcli.optimize import configuration
import shutil

shutil.rmtree('ensemble', ignore_errors=True)
configuration('config_pysot.yaml')