import numpy as np


def uniform_random_sample(H, persis_info, gen_specs, _):
    """
    Generates ``gen_specs['user']['gen_batch_size']`` points uniformly over the domain
    defined by ``gen_specs['user']['ub']`` and ``gen_specs['user']['lb']``.

    .. seealso::
        `test_uniform_sampling.py <https://github.com/Libensemble/libensemble/blob/develop/libensemble/tests/regression_tests/test_uniform_sampling.py>`_ # noqa
    """
    ub = gen_specs['user']['ub']
    lb = gen_specs['user']['lb']

    n = len(lb)
    b = gen_specs['user']['gen_batch_size']

    H_o = np.zeros(b, dtype=gen_specs['out'])

    H_o['x'] = persis_info['rand_stream'].uniform(lb, ub, (b, n))

    return H_o, persis_info