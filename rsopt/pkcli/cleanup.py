import os
import re

_LIBE_CLEANUP_FILES = ['ensemble.log', 'libE_stats.txt']
_LIBE_CLEANUP_PATTERNS = [['libE_history', '.npy'], ['libE_persis_info', '.pickle']]


def _matches(name, patterns):
    """
    If name matches any pattern in patterns return True
    :param name: (str) Any string
    :param patterns: (iter) Iterable that contains iterables of strings that define prefix and suffix patterns to
    match to. Prefix or suffix may be empty.
    :return: (bool)
    """

    for p in patterns:
        prefix, suffix = p + (len(p) == 1) * ['']
        pattern = r'^({prefix}).*({suffix})$'.format(prefix=prefix, suffix=suffix)
        matches = bool(re.search(pattern, name))
        if matches:
            return True

    return False


def libensemble(directory=None):
    """
    Clean a directory of libEnsemble output files. Defaults to the current working directory.
    This will delete all files that match:
      'ensemble.log'
      'libE_stats.txt'
      .npy files starting with 'libE_history'
      .pickle files starting with 'libE_persis_info'

    :param directory: (str) Optional. Path to directory that will be cleaned.
    :return:
    """
    directory = '.' if not directory else directory
    for file in os.listdir(directory):
        if file in _LIBE_CLEANUP_FILES:
            path = os.path.join(directory, file)
            os.remove(path)
        if _matches(file, _LIBE_CLEANUP_PATTERNS):
            path = os.path.join(directory, file)
            os.remove(path)