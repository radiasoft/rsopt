import pickle
import pathlib

# Set path accordingly
PATH = pathlib.Path('.')
Q114 = 'Q114_r56_to_k1.pickle'
Q115 = 'Q115_r56_to_k1.pickle'
Q116 = 'Q116_r56_to_k1.pickle'


def passes(target_r56):
    return 0


def get_quads_k1(J):
    r56 = J['inputs']['target_r56']
    print("target r56:", r56)
    
    fq114 = pickle.load(open(PATH.joinpath(Q114), 'rb'))
    fq115 = pickle.load(open(PATH.joinpath(Q115), 'rb'))
    fq116 = pickle.load(open(PATH.joinpath(Q116), 'rb'))
    
    J['QUADS'] = {
        'Q114': fq114(r56),
        'Q115': fq115(r56),
        'Q116': fq116(r56),
    }

    print(f'QUAD SETTINGS for {r56}', J['QUADS'])


def set_quads_k1(J):
    for q in ['Q114', 'Q115', 'Q116']:
        J['inputs'][f'{q}.K1'] = J['QUADS'][q]