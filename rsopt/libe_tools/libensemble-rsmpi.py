#!/usr/bin/env python
import argparse
import subprocess
import sys
import time

run_string = 'rsmpi -n {n} -h {h} {t_flag} {args}'
t_flag = '-t {t}'

parser = argparse.ArgumentParser(description="Wrap rsmpi for use by libensemble. Converts required MPICH flags"
                                             "to rsmpi flags.")

parser.add_argument("-np", dest="n", required=True,
                    help="Pass number of processors to rsmpi")
parser.add_argument("--ppn", dest="t", required=False,
                    help="Number of processes per node to use")
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


def stream_process(process):
    go = process.poll() is None
    for line in process.stdout:
        sys.stdout.write(line.decode())
        sys.stdout.flush()
    for line in process.stderr:
        sys.stderr.write(line.decode())
        sys.stderr.flush()
    return go


parsed_args = parser.parse_args()
if parsed_args.machinefile is not None:
    h = get_host_from_machinefile(parsed_args.machinefile)
else:
    h = parsed_args.hosts
args = ' '.join(parsed_args.args)

formatted_run_string = run_string.format(n=parsed_args.n, h=h,
                                         t_flag=t_flag.format(t=parsed_args.t) if parsed_args.t else '',
                                         args=args).split()

# Execute
try:
    run_status = subprocess.Popen(formatted_run_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while stream_process(run_status):
        time.sleep(0.001)

    # Handle any final write
    out, err = run_status.communicate()
    if out:
        sys.stdout.write(out.decode())
        sys.stdout.flush()
    if err:
        sys.stderr.write(err.decode())
        sys.stderr.flush()
    sys.exit(run_status.returncode)

except KeyboardInterrupt:
    run_status.kill()
    out, err = run_status.communicate()
    sys.stdout.write(out.decode())
    sys.stderr.write(err.decode())
    sys.stderr.flush()
    sys.exit(run_status.returncode)
