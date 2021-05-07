#!/usr/bin/env python
import argparse
import subprocess
import sys

run_string = 'rsmpi -n {n} -h {h} {args}'

parser = argparse.ArgumentParser(description="Wrap rsmpi for use by libensemble. Converts required MPICH flags"
                                             "to rsmpi flags.")

parser.add_argument("-np", dest="n", required=True,
                     help="Pass number of processors to rsmpi")
parser.add_argument("--ppn", dest="ppn", required=False,
                    help="Not required by rsmpi, but supplied by libEnsemble. Input is not used if given.")
parser.add_argument('args', nargs=argparse.REMAINDER, help="All other arguments are appended after rsmpi")
server_spec = parser.add_mutually_exclusive_group(required=True)
server_spec.add_argument("-machinefile", dest="machinefile",
                    help="Location of machinefile that gives rsmpi server number on the first line")
server_spec.add_argument("-hosts", dest="hosts",
                    help="Host number of rsmpi server")

def get_host_from_machinefile(machinefile):
    with open(machinefile) as ff:
        host = ff.readline().strip()

    return host


parsed_args = parser.parse_args()
if parsed_args.machinefile is not None:
    h = get_host_from_machinefile(parsed_args.machinefile)
else:
    h = parsed_args.hosts
args = ' '.join(parsed_args.args)

formatted_run_string = run_string.format(n=parsed_args.n, h=h, args=args).split()

# Execute
run_status = subprocess.Popen(formatted_run_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

out, err = run_status.communicate()

if out:
    sys.stdout.write(out.decode())
    sys.stdout.flush()
if err:
    sys.stderr.write(err.decode())
    sys.stderr.flush()
    sys.exit(1)
sys.exit(0)