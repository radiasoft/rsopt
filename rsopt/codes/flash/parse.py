import re

def parse_file(par_path: str) -> dict:
    """Read in a FLASH .par file and return a dictionary of parameters and values."""

    res = {}
    par_text = open(par_path)

    for line in par_text.readlines():
        line = re.sub(r"#.*$", "", line)
        m = re.search(r"^(\w.*?)\s*=\s*(.*?)\s*$", line)
        if m:
            f, v = m.group(1, 2)
            res[f.lower()] = v
    return res