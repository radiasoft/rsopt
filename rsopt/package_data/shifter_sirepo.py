import pickle
import sys
import sirepo.lib

CODE, FILE = sys.argv[1:]

t = sirepo.lib.Importer(CODE).parse_file(FILE)
sys.stdout.buffer.write(pickle.dumps(t))