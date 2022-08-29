Examples
========



.. toctree::
   :maxdepth: 1
   :glob:

   examples/*

..
   * :doc:`Elegant Matching Parallel Execution<examples/elegant_parallel>`
   * :doc:`MOBO<examples/mobo>`
   * :doc:`Multi-code<examples/multi>`
   * :doc:`APOSMM<examples/aposmm>`
   * :doc:`CHWIRUT<examples/chwirut>`
   * :doc:`Radia Undulator<examples/radia_undulator>`
   * :doc:`Quickstart<examples/quickstart>`
   * :doc:`Sampler<examples/sampler>`
..
   include:: elegant_matching_parallel_execution_example
   include:: python_chwirut_example
   include:: mobo_example
   include:: python_radia_undulator_example
   include:: multi_code_example
   include:: quickstart_example
   include:: python_aposmm_example
   include:: sampler_restart

..
  elegant_matching_parallel_execution_example
  codes:
    - elegant:
        settings:
            bunched_beam.n_particles_per_bunch: 16384
        parameters:
          Q1.K1:
            min: 8.
            max: 12.
            start: 10.
          Q2.K1:
  mobo_example
  ==> mobo_example/config_mobo_osy.yml <==
  codes:
    - python:
        parameters:
          x1:
            min: 0.
            max: 10.
            start: 1.0
          x2:
            min: 0.
            max: 10.

  ==> mobo_example/config_mobo.yml <==
  codes:
    - python:
        parameters:
          x1:
            min: 0.
            max: 3.14
            start: 1.0
          x2:
            min: 0.
            max: 3.14
  multi_code_example
  codes:
      # OPAL Block for adjusting capture cavity settings
      - opal:
          settings:
              # Shorten tracking to just after X106 monitor
              track.zstop: "{0.28,8.25}"
              beam.bcurrent: 1.3  # Sets bunch to be 1 nC of charge
          parameters:
              DISTRIBUTION.1.TPULSEFWHM:
                  min: 2.5e-11
  python_aposmm_example
  head: cannot open 'python_aposmm_example/*.yml' for reading: No such file or directory
  python_chwirut_example
  head: cannot open 'python_chwirut_example/*.yml' for reading: No such file or directory
  python_radia_undulator_example
  # Top level key is `codes` which should be a list (note the dash in front of `- python`) of codes to be executed to complete an evaluation
  codes:
      - python:
          # `settings` is an optional bookkeeping key. Values listed are always passed each execution.
          # `settings` can also be used to set dummy values that are filled in by a pre-process function
          #   at run time. This is illustrated in this example if serial execution is used (make sure to uncomment the `preprocess` line below in that case)
          settings:
              _gap: 4.0 
              _gap_ofst: 0.0
              _nper: 15 
  quickstart_example
  codes:
    - python:
        parameters:
          x:
            min: -3.
            max: 3.
            start: 0.08
          y:
            min: -2.
            max: 2.
  sampler_restart
  codes:
      - python:
          settings:
              a: 1.0
          parameters:
              x: 
                  min: -2            
                  max:  2            
                  start: 1.2  
                  samples: 50
