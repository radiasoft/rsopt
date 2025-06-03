def f_pre(J):
    # Example pre processing to modify the number of particles used
    particles = J['inputs']['bunched_beam.n_particles_per_bunch']
    J['inputs']['bunched_beam.n_particles_per_bunch'] = particles // 4
