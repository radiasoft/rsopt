from rsopt.pkcli.sample import start
import shutil
import time

if __name__ == "__main__":
    shutil.rmtree('ensemble', ignore_errors=True)
    t1 = time.time()
    start('config.yml')
    print("Run time", time.time() - t1)
