import unittest
import numpy as np
import os
from rsopt.pkcli.optimize import configuration
from rsopt.pkcli import cleanup
from rsopt import _EXAMPLE_SYMLINK, _EXAMPLE_REGISTRY
from pykern import pkyaml
import shutil
import glob

_EXAMPLES = pkyaml.load_file(_EXAMPLE_REGISTRY)['examples']


def copy_example_files(example):
    example_file_list = example['files']
    for filename in example_file_list:
        filepath = os.path.join(_EXAMPLE_SYMLINK, filename)
        shutil.copyfile(filepath, filename, follow_symlinks=True)

    return example_file_list


def run_test(config_filename):
    configuration(config_filename)


def run_cleanup(file_list):
    shutil.rmtree('ensemble', ignore_errors=True)
    cleanup.libensemble('.')
    if file_list:
        for file in file_list:
            if os.path.exists(file):
                os.remove(file)
    try:
        history_file = glob.glob('H_*.npy')[0]
        os.remove(history_file)
    except IndexError:
        pass
    try:
        history_pkl = glob.glob('H_*.pickle')[0]
        os.remove(history_pkl)
    except IndexError:
        pass


def get_test_result():
    history_file = glob.glob('H_*.npy')[0]
    ff = np.load(history_file)
    return np.min(ff['f'][:])


class TestExamples(unittest.TestCase):
    def test_all(self):
        for i, example in enumerate(_EXAMPLES.values()):
            # If running with Pycharm test configuration make sure to use unittests
            with self.subTest(i=i):
                self.file_list = copy_example_files(example)
                config_filename = self.file_list[-1]
                run_test(config_filename)
                test_result = get_test_result()
                run_cleanup(self.file_list)

                error_msg = f'Test of {config_filename} failed'

                self.assertTrue(np.all(np.isclose(example['result'], test_result)), msg=error_msg)

    def tearDown(self):
        try:
            run_cleanup(self.file_list)
        except NameError:
            run_cleanup(None)



