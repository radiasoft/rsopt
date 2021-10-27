.. _options_ref:
Options
=======

- `software` [str]:
    Specify what software package to use when rsopt runs. See :ref:`Software</opt_software>` for a list of supported software.
- `method` [str]:
    When `software` package chosen contains multiple algorithms the choice is specified by `method`. See :ref:`Software</opt_software>` for particular supported by the chosen `software`.
- `software_options` [dict]:
    Can be used to pass configuration options directly to the chosen `software`. See :ref:`Software</opt_software>` for available options that can be set depending on chosen `software`.
- `nworkers` [int] (default: 2):
    Number of workers used for running simulations, and in some cases a worker may be used run the governing `software`. In cases where the `software` option supports parallel evaluations then workers will each, independently run through a Job chain. See :ref:`Software</opt_software>` for information on support for parallel evaluation in a particular `software` option.