# fodo_opt
execution_mode = 'serial'

lattice_file = """

"D1": DRIF,l=0.5
"D2": DRIF,l=1
"Q1": QUAD,k1=5,l=0.25
"Q2": QUAD,k1=-5,l=0.25
"FODO": LINE=(D1,Q1,D2,Q2,D1)

"""

elegant_file = """

&global_settings
  mpi_io_write_buffer_size = 1048576,
&end

&run_setup
  semaphore_file = run_setup.semaphore,
  centroid = "run_setup.centroid.sdds",
  element_divisions = 20,
  final = "run_setup.final.sdds",
  lattice = "elegant.lte",
  output = "run_setup.output.sdds",
  p_central_mev = 1001,
  parameters = "run_setup.parameters.sdds",
  print_statistics = 1,
  sigma = "run_setup.sigma.sdds",
  use_beamline = "fodo",
&end

&run_control
&end

&twiss_output
  filename = "twiss_output.filename.sdds",
&end

&optimization_setup
  tolerance = -0.0001,
  log_file = optimization_setup.log_file.sdds
&end

&optimization_term
  term = "nux 0.25 - sqr",
&end

&optimization_term
  term = "nuy 0.25 - sqr",
&end

&optimization_variable
  item = "K1",
  lower_limit = -15,
  name = "Q1",
  upper_limit = 15,
&end

&optimization_variable
  item = "K1",
  lower_limit = -15,
  name = "Q2",
  upper_limit = 15,
&end

&bunched_beam
  alpha_x = 1,
  alpha_y = 1,
  alpha_z = 0,
  beta_x = 10,
  beta_y = 10,
  beta_z = 0,
  bunch = "bunched_beam.bunch.sdds",
  distribution_cutoff[0] = 3, 3, 3,
  emit_x = 4.6e-08,
  emit_y = 4.6e-08,
  emit_z = 0,
  enforce_rms_values[0] = 1, 1, 1,
  one_random_bunch = 0,
  sigma_dp = 0.001,
  sigma_s = 0.00065,
  symmetrize = 1,
  use_twiss_command_values = 1,
&end

&optimize
&end

&save_lattice
  filename = "save_lattice.filename.lte",
&end

&run_setup
  semaphore_file = run_setup.semaphore,
  lattice = "save_lattice.filename.lte",
  p_central_mev = 1001,
  use_beamline = "fodo",
&end

&run_control
&end

&twiss_output
  filename = "twiss_output2.filename.sdds",
&end

"""

with open('../../tests/support/elegant.lte', 'w') as f:
    f.write(lattice_file)

with open('../../tests/support/elegant.ele', 'w') as f:
    f.write(elegant_file)

import os
os.system('elegant elegant.ele')
