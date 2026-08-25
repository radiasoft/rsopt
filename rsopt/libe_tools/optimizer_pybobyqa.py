import numpy as np
from rsopt.libe_tools import tools
from rsopt.libe_tools import optimizer
from rsopt.libe_tools.generator_functions.persistent_pybobyqa import persistent_pybobyqa
from libensemble.alloc_funcs.start_only_persistent import only_persistent_gens


# dimension for x set at run time
pybobyqa_gen_out = [('x', float, None), ('instance', int)]


class PybobyqaOptimizer(optimizer.libEnsembleOptimizer):

    def __init__(self, config_model):
        super().__init__(config_model)

    def _configure_optimizer(self):
        gen_out = [tools.set_dtype_dimension(dtype, self._config.dimension) for dtype in pybobyqa_gen_out]
        software_options = self._config.options.software_options.model_dump()

        # One instance per simulation worker unless the user asked for a specific number
        requested_instances = software_options.pop('instances', None)
        instances = requested_instances or max(self._config.options.nworkers - 1, 1)
        additional_starts = self._validate_additional_starts(
            software_options.pop('additional_instance_starts'), instances, requested_instances)

        user_keys = {'lb': self._config.lower_bounds,
                     'ub': self._config.upper_bounds,
                     'dim': self._config.dimension,
                     'xstart': self._config.start,
                     'instances': instances,
                     'additional_instance_starts': additional_starts,
                     **software_options}

        self.gen_specs.update({'gen_f': persistent_pybobyqa,
                               'persis_in': self._config.options.method.persis_in +
                                            [n[0] for n in gen_out],
                               'out': gen_out,
                               'user': user_keys})

    def _validate_additional_starts(self, starts, instances, requested_instances):
        """Check user-supplied instance start points against the instance count, dimension and bounds.

        This cannot live on the Pydantic options model: neither the problem dimension nor the
        resolved instance count is visible there, since `instances` may default to nworkers-1.
        """
        if not starts:
            return []

        if len(starts) > instances - 1:
            if requested_instances:
                source = '`instances` is set to {}'.format(instances)
            else:
                source = ('`instances` was not given, so it defaults to nworkers-1 = {}'
                          .format(instances))
            raise ValueError(
                'additional_instance_starts lists {} starting point(s), but at most {} may be '
                'given: instance 0 always starts from the `start` values of the parameters, '
                'leaving instances-1 = {} to be set explicitly ({}).'
                .format(len(starts), instances - 1, instances - 1, source))

        dimension = self._config.dimension
        lower_bounds, upper_bounds = self._config.lower_bounds, self._config.upper_bounds

        checked = []
        for i, point in enumerate(starts):
            if len(point) != dimension:
                raise ValueError(
                    'additional_instance_starts entry {} has {} value(s), but this problem has '
                    'dimension {}. Starting points are given in the flattened parameter vector, '
                    'so multi-dimensional parameters contribute more than one value each.'
                    .format(i, len(point), dimension))

            point = np.array(point, dtype=float)
            outside = np.flatnonzero((point < lower_bounds) | (point > upper_bounds))
            if outside.size:
                raise ValueError(
                    'additional_instance_starts entry {} lies outside the parameter bounds at '
                    'index(es) {}: value(s) {} not within lower bounds {} and upper bounds {}.'
                    .format(i, outside.tolist(), point[outside].tolist(),
                            np.asarray(lower_bounds)[outside].tolist(),
                            np.asarray(upper_bounds)[outside].tolist()))
            checked.append(point)

        return checked

    def _configure_allocation(self):
        self.alloc_specs.update({'alloc_f': only_persistent_gens,
                                 'out': [('given_back', bool)],
                                 'user': {'async_return': True, 'active_recv_gen': True}})

    def _configure_specs(self):
        self.nworkers = self._config.options.nworkers
        super(PybobyqaOptimizer, self)._configure_specs()
