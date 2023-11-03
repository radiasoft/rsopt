#!/usr/bin/env python
import argparse
import selectors
import subprocess
import sys

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
    sel = selectors.DefaultSelector()
    sel.register(run_status.stdout, selectors.EVENT_READ)
    sel.register(run_status.stderr, selectors.EVENT_READ)

    while True:
        for key, _ in sel.select():
            data = key.fileobj.read1().decode()
            if not data:
                run_status.poll()
                sys.exit(run_status.returncode)
            if key.fileobj is run_status.stdout:
                print(data, end="", file=sys.stdout, flush=True)
            else:
                print(data, end="", file=sys.stderr, flush=True)
except KeyboardInterrupt:
    try:
        run_status.kill()
        out, err = run_status.communicate()
        sys.stdout.write(out.decode())
        sys.stderr.write(err.decode())
        sys.stderr.flush()
    except NameError:
        sys.exit(1)