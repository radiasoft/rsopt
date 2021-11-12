import re
import pandas

LIBE_STATS_FIELDS = ["Worker", ": sim_id", ": sim Time:", "Start:", "End:", "Status:", "\n"]
DATAFRAME_COLUMNS = ["worker", "sim_id", "time", "start", "end", "status"]
LIBE_STATS_PATTERN = '(?<={})(.+?)(?={})'


def create_empty_persis_info(libE_specs):
    """
    Create `persis_info` for libEnsemble if no persistent data needs to be transfered.
    :param libE_specs: `libE_specs` datastructure.
    :return:
    """
    nworkers = libE_specs['nworkers']
    persis_info = {i: {'worker_num': i} for i in range(1, nworkers+1)}

    return persis_info


def _libe_stat_regex():
    fp = []
    for i in range(1, len(LIBE_STATS_FIELDS)):
        p = LIBE_STATS_PATTERN.format(LIBE_STATS_FIELDS[i - 1], LIBE_STATS_FIELDS[i])
        fp.append(p)

    return re.compile("|".join(fp))


def parse_stat_file(filename):
    """
    Parses libE_stats.txt from a libEnsemble run and formats the data into a Pandas DataFrame.

    :param filename: (str) File name (usually libE_stats.txt)
    :return: Returns a Pandas DataFrame
    """
    parsed_lines = []
    line_parse = _libe_stat_regex()

    with open(filename, 'r') as ff:
        for line in ff.readlines():
            p = line_parse.findall(line)
            f = []
            for r in p:
                f.append(''.join(r).strip())
            parsed_lines.append(f)

    df = pandas.DataFrame(parsed_lines, columns=DATAFRAME_COLUMNS)

    return df
