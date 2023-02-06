"""Script is called inside Shifter container with Sirepo installed and returns parsed model information"""
import pickle
import sys
import sirepo.lib

CODE, FILE, *IGNORE_LIST = sys.argv[1:]

t = sirepo.lib.Importer(CODE, IGNORE_LIST).parse_file(FILE)
sys.stdout.buffer.write(pickle.dumps(t))
