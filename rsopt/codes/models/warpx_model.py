from typing import Optional, List, Dict, Literal
from pydantic import BaseModel
from typing import Type

# ---------------------------
# Top-level / Misc parameters
# ---------------------------

class Misc(BaseModel):
    authors: Optional[str] = None
    max_step: Optional[int] = None
    stop_time: Optional[float] = None
    # Any other bare (no-group) keys can be added here


# ---------------------------
# Geometry & AMR / mesh setup
# ---------------------------

class Amr(BaseModel):
    n_cell: Optional[List[int]] = None
    max_level: Optional[int] = None
    ref_ratio: Optional[List[int]] = None
    ref_ratio_vect: Optional[List[List[int]]] = None
    max_grid_size: Optional[int] = None  # docs: Distribution across MPI ranks



class Geometry(BaseModel):
    prob_lo: Optional[List[float]] = None
    prob_hi: Optional[List[float]] = None
    is_periodic: Optional[List[int]] = None  # length = dim, 0/1
    # Add other geometry.* keys as needed


# ---------------------------------
# Domain boundaries & PML / EB
# ---------------------------------

BoundaryFieldBC = Literal["pml", "periodic", "absorbing_silver_mueller"]
# See docs for options; Silver-Mueller only with Yee solver. :contentReference[oaicite:1]{index=1}

class Boundary(BaseModel):
    field_lo: Optional[List[BoundaryFieldBC]] = None
    field_hi: Optional[List[BoundaryFieldBC]] = None


class Pml(BaseModel):
    # Additional PML-related toggles kept optional
    do_pml_dive_cleaning: Optional[int] = None  # must match do_pml_divb_cleaning when set
    do_pml_divb_cleaning: Optional[int] = None  # see docs discussion. :contentReference[oaicite:2]{index=2}


class EmbeddedBoundary(BaseModel):
    eb_implicit_function: Optional[str] = None
    stl_file: Optional[str] = None
    # Add other EB inputs as needed. :contentReference[oaicite:3]{index=3}


# ---------------------------------
# Parallelization & constants
# ---------------------------------

class Parallel(BaseModel):
    # placeholder for distribution across MPI ranks, etc.
    pass

# class MyConstants(BaseModel):
#     # user-defined constants, free-form names → values via AMReX parser
#     # Represented as a simple mapping the app can parse/expand as needed.
#     values: Optional[Dict[str, float]] = None  # e.g. {"a0": 3.0}
#     # Math parser usage for RHS expressions is documented. :contentReference[oaicite:4]{index=4}


# ---------------------------------
# Moving window & refinement helpers
# ---------------------------------

class WarpxMovingWindow(BaseModel):
    do_moving_window: Optional[int] = None
    moving_window_dir: Optional[Literal["x", "y", "z"]] = None
    moving_window_v: Optional[float] = None
    start_moving_window_step: Optional[int] = None
    end_moving_window_step: Optional[int] = None  # -1 = disabled
    # Fine-tag patch (static refinement box):
    fine_tag_lo: Optional[List[float]] = None
    fine_tag_hi: Optional[List[float]] = None
    ref_patch_function: Optional[str] = None
    refine_plasma: Optional[int] = None
    n_current_deposition_buffer: Optional[int] = None
    n_field_gather_buffer: Optional[int] = None
    do_single_precision_comms: Optional[int] = None
    # Mesh-refinement interaction with particles:
    # these are particle-name lists
    # keep in Particles container too; duplicate allowed by design
    # (either place is fine for validation)
    # See docs text around these items. :contentReference[oaicite:5]{index=5}


# ---------------------------------
# WarpX global & external fields
# ---------------------------------

class Warpx(BaseModel):
    used_inputs_file: Optional[str] = None
    gamma_boost: Optional[float] = None
    boost_direction: Optional[Literal["x", "y", "z"]] = None
    zmax_plasma_to_compute_max_step: Optional[float] = None
    compute_max_step_from_btd: Optional[int] = None
    random_seed: Optional[str | int] = None
    grid_type: Optional[Literal["collocated", "staggered", "hybrid"]] = None  # default staggered.

    # External fields applied to the grid:
    B_ext_grid_init_style: Optional[Literal["constant", "parse_B_ext_grid_function", "read_from_file"]] = None
    E_ext_grid_init_style: Optional[Literal["constant", "parse_E_ext_grid_function", "read_from_file"]] = None
    B_external_grid: Optional[List[float]] = None  # 3 floats
    E_external_grid: Optional[List[float]] = None  # 3 floats
    Bx_external_grid_function: Optional[str] = None
    By_external_grid_function: Optional[str] = None
    Bz_external_grid_function: Optional[str] = None
    Ex_external_grid_function: Optional[str] = None
    Ey_external_grid_function: Optional[str] = None
    Ez_external_grid_function: Optional[str] = None
    read_fields_from_path: Optional[str] = None
    maxlevel_extEMfield_init: Optional[int] = None
    # Divergence cleaning, projection, and hybrid QED toggles:
    do_initial_div_cleaning: Optional[int] = None
    projection_div_cleaner_rtol: Optional[float] = None
    projection_div_cleaner_atol: Optional[float] = None
    use_hybrid_QED: Optional[bool] = None
    quantum_xi: Optional[float] = None
    # See external field & additional parameter sections. :contentReference[oaicite:7]{index=7}


# ---------------------------------
# Numerics & algorithms
# ---------------------------------

MaxwellSolver = Literal["yee", "ckc", "psatd", "ect", "hybrid", "none"]
EMMedium = Literal["vacuum", "macroscopic"]
CurrentDeposition = Literal["direct", "esirkepov", "villasenor", "vay"]

class Algo(BaseModel):
    evolve_scheme: Optional[Literal["explicit", "theta_implicit_em", "semi_implicit_em"]] = None
    maxwell_solver: Optional[MaxwellSolver] = None
    em_solver_medium: Optional[EMMedium] = None
    # PSATD/macroscopic/hybrid families have many sub-keys.
    # Keep containers below to collect them when present.

    # current deposition & related:
    current_deposition: Optional[CurrentDeposition] = None  # options per docs. :contentReference[oaicite:8]{index=8}
    load_balance_intervals: Optional[int] = None
    load_balance_efficiency_ratio_threshold: Optional[float] = None
    load_balance_with_sfc: Optional[bool] = None
    load_balance_knapsack_factor: Optional[float] = None
    load_balance_costs_update: Optional[Literal["heuristic", "timers"]] = None
    costs_heuristic_particles_wt: Optional[float] = None
    costs_heuristic_cells_wt: Optional[float] = None



class Macroscopic(BaseModel):
    # If medium = macroscopic
    sigma_function: Optional[str] = None
    epsilon_function: Optional[str] = None
    mu_function: Optional[str] = None
    sigma: Optional[float] = None
    epsilon: Optional[float] = None
    mu: Optional[float] = None
    # :contentReference[oaicite:9]{index=9}


class HybridPICModel(BaseModel):
    elec_temp: Optional[float] = None
    n0_ref: Optional[float] = None
    gamma: Optional[float] = None
    plasma_resistivity: Optional[float | str] = None
    plasma_hyper_resistivity: Optional[float | str] = None
    Jx_external_grid_function: Optional[str] = None
    Jy_external_grid_function: Optional[str] = None
    Jz_external_grid_function: Optional[str] = None
    n_floor: Optional[float] = None
    substeps: Optional[int] = None
    holmstrom_vacuum_region: Optional[bool] = None
    add_external_fields: Optional[bool] = None
    # External time-varying vector potentials
    # Represent as a dict keyed by field name to keep it general
    external_vector_potential_fields: Optional[List[str]] = None
    # Each name then maps to path/functions:
    ext_vec_potential_read_from_file: Optional[Dict[str, bool]] = None
    ext_vec_potential_path: Optional[Dict[str, str]] = None
    ext_vec_Ax_function: Optional[Dict[str, str]] = None
    ext_vec_Ay_function: Optional[Dict[str, str]] = None
    ext_vec_Az_function: Optional[Dict[str, str]] = None
    ext_vec_A_time_function: Optional[Dict[str, str]] = None
    # :contentReference[oaicite:10]{index=10}


class ImplicitEvolve(BaseModel):
    theta: Optional[float] = None
    nonlinear_solver: Optional[Literal["picard", "newton", None]] = None

class Picard(BaseModel):
    verbose: Optional[bool] = None
    require_convergence: Optional[bool] = None
    maximum_iterations: Optional[int] = None
    relative_tolerance: Optional[float] = None
    absolute_tolerance: Optional[float] = None
    diagnostic_file: Optional[str] = None
    diagnostic_interval: Optional[int] = None

class Newton(BaseModel):
    verbose: Optional[bool] = None
    require_convergence: Optional[bool] = None
    maximum_iterations: Optional[int] = None
    relative_tolerance: Optional[float] = None
    absolute_tolerance: Optional[float] = None
    diagnostic_file: Optional[str] = None
    diagnostic_interval: Optional[int] = None
    # GMRES suboptions
    gmres_verbose_int: Optional[int] = None
    gmres_restart_length: Optional[int] = None
    gmres_maximum_iterations: Optional[int] = None
    gmres_relative_tolerance: Optional[float] = None
    gmres_absolute_tolerance: Optional[float] = None

class ImplicitParticleSolve(BaseModel):
    max_particle_iterations: Optional[int] = None
    particle_tolerance: Optional[float] = None
    particle_suborbits: Optional[bool] = None
    print_unconverged_particle_details: Optional[bool] = None

class Preconditioner(BaseModel):
    pc_type: Optional[Literal["pc_curl_curl_mlmg", "pc_jacobi", None]] = None
    # curl-curl MLMG options:
    pc_curl_curl_mlmg_verbose: Optional[bool] = None
    pc_curl_curl_mlmg_bottom_verbose: Optional[bool] = None
    pc_curl_curl_mlmg_agglomeration: Optional[bool] = None
    pc_curl_curl_mlmg_consolidation: Optional[bool] = None
    pc_curl_curl_mlmg_max_iter: Optional[int] = None
    pc_curl_curl_mlmg_max_coarsening_level: Optional[int] = None
    pc_curl_curl_mlmg_relative_tolerance: Optional[float] = None
    pc_curl_curl_mlmg_absolute_tolerance: Optional[float] = None
    # jacobi options:
    pc_jacobi_verbose: Optional[bool] = None
    pc_jacobi_max_iter: Optional[int] = None
    pc_jacobi_relative_tolerance: Optional[float] = None
    pc_jacobi_absolute_tolerance: Optional[float] = None

class ImplicitConfig(BaseModel):
    implicit_evolve: Optional[ImplicitEvolve] = None
    picard: Optional[Picard] = None
    newton: Optional[Newton] = None
    particle_solve: Optional[ImplicitParticleSolve] = None
    use_mass_matrices_jacobian: Optional[bool] = None
    use_mass_matrices_pc: Optional[bool] = None
    preconditioner: Optional[Preconditioner] = None
    # Summary of implicit knobs from docs. :contentReference[oaicite:11]{index=11}


# ---------------------------------
# Particles: static container + dynamic species models
# ---------------------------------

FieldGathering = Literal["energy-conserving", "momentum-conserving"]
ParticlePusher = Literal["boris", "vay", "higuera_cary"]  # commonly used; keep optional
ParticleInjectionStyle = Literal[
    "none", "gaussian_beam", "nrandom", "random_per_cell", "from_file",
    "uniform", "read_from_file", "rigid_injection"
]  # include common styles; keep open

class Particles(BaseModel):
    species_names: Optional[List[str]] = None
    photon_species: Optional[List[str]] = None
    use_fdtd_nci_corr: Optional[int] = None
    rigid_injected_species: Optional[List[str]] = None
    do_tiling: Optional[bool] = None
    # Mesh refinement interactions (also mentioned with warpx.*):
    deposit_on_main_grid: Optional[List[str]] = None
    gather_from_main_grid: Optional[List[str]] = None
    particle_shape: Optional[int] = None  # order 1..4; required if any species/laser present. :contentReference[oaicite:12]{index=12}
    max_grid_crossings: Optional[int] = None


class Species(BaseModel):
    # name of the group is dynamic; this model covers <species_name>.*
    species_type: Optional[str] = None  # e.g., electron, proton, etc.
    charge: Optional[float] = None
    mass: Optional[float] = None

    # Initialization / injection:
    injection_style: Optional[ParticleInjectionStyle] = None
    density: Optional[float] = None
    density_function: Optional[str] = None
    profile: Optional[str] = None
    momentum_distribution_type: Optional[
        Literal["fixed_u", "gaussian", "maxwell_boltzmann", "maxwell_juttner", "radial_expansion", "parse_momentum_function"]
    ] = None
    ux: Optional[float] = None
    uy: Optional[float] = None
    uz: Optional[float] = None
    temperature: Optional[float] = None  # representative
    beta_distribution_type: Optional[Literal["constant"]] = None
    beta: Optional[float] = None
    bulk_vel_dir: Optional[Literal["+x", "+y", "+z", "-x", "-y", "-z", "x", "y", "z"]] = None
    momentum_function_ux: Optional[str] = None
    momentum_function_uy: Optional[str] = None
    momentum_function_uz: Optional[str] = None
    initialize_self_fields: Optional[int] = None
    self_fields_required_precision: Optional[float] = None

    # Algorithms:
    pusher: Optional[ParticlePusher] = None
    field_gathering: Optional[FieldGathering] = None

    # Ionization / QED:
    do_field_ionization: Optional[int] = None
    adk_prefactor_multiplier: Optional[float] = None
    use_zbl_ionization: Optional[int] = None
    use_ZLL_correction: Optional[int] = None
    physical_element: Optional[str] = None
    ionization_product_species: Optional[str] = None
    ionization_initial_level: Optional[int] = None
    do_classical_radiation_reaction: Optional[int] = None
    do_qed_quantum_sync: Optional[int] = None
    do_qed_breit_wheeler: Optional[int] = None
    # See species & initialization sections. :contentReference[oaicite:13]{index=13}


# ---------------------------------
# Lasers: static container + dynamic laser models
# ---------------------------------

class Lasers(BaseModel):
    names: Optional[List[str]] = None


LaserProfile = Literal["Gaussian", "parse_field_function", "from_lasy_file", "from_binary_file"]

class Laser(BaseModel):
    # <laser_name>.*
    position: Optional[List[float]] = None
    direction: Optional[List[float]] = None
    polarization: Optional[List[float]] = None
    e_max: Optional[float] = None
    a0: Optional[float] = None
    wavelength: Optional[float] = None
    waist: Optional[float] = None
    profile: Optional[LaserProfile] = None
    field_function: Optional[str] = None
    file: Optional[str] = None
    antenna_evolution: Optional[Literal["static", "moving", "continuous_injection"]] = None
    continuous_injection: Optional[int] = None
    # See laser section re: profiles & boosted frame notes. :contentReference[oaicite:14]{index=14}


# ---------------------------------
# External fields applied to particles
# ---------------------------------

ParticleFieldStyle = Literal[
    "none",
    "constant",
    "parse_E_ext_particle_function",
    "parse_B_ext_particle_function",
    "repeated_plasma_lens",
]

class ParticlesExternalFields(BaseModel):
    E_ext_particle_init_style: Optional[ParticleFieldStyle] = None
    B_ext_particle_init_style: Optional[ParticleFieldStyle] = None
    E_external_particle: Optional[List[float]] = None
    B_external_particle: Optional[List[float]] = None
    Ex_external_particle_function: Optional[str] = None
    Ey_external_particle_function: Optional[str] = None
    Ez_external_particle_function: Optional[str] = None
    Bx_external_particle_function: Optional[str] = None
    By_external_particle_function: Optional[str] = None
    Bz_external_particle_function: Optional[str] = None
    # Repeated plasma lens parameters (placed generically):
    # strength, start_z, end_z etc. can be added as needed
    read_fields_from_path: Optional[str] = None
    # :contentReference[oaicite:15]{index=15}


# ---------------------------------
# Diagnostics (containers; many knobs)
# ---------------------------------

class Diagnostics(BaseModel):
    # Add common keys like diagnostics.names, plot_int, etc., if desired
    pass

class FullDiagnostics(BaseModel):
    # <diag_name>.* (full diagnostics)
    frequency: Optional[int] = None
    file_prefix: Optional[str] = None
    fields_to_plot: Optional[List[str]] = None
    particle_fields_to_plot: Optional[List[str]] = None
    particle_fields_species: Optional[List[str]] = None
    # Including per-field knobs like <field_name>.do_average as a mapping:
    particle_fields_do_average: Optional[Dict[str, int]] = None
    # See notes on required particle_shape and field lists. :contentReference[oaicite:16]{index=16}

class TimeAveragedDiagnostics(BaseModel):
    # <diag_name>.* (time-averaged)
    frequency: Optional[int] = None
    file_prefix: Optional[str] = None

class BackTransformedDiagnostics(BaseModel):
    # container for BTD-specific parameters
    # warpx.compute_max_step_from_btd can be used to auto-extend runtime. :contentReference[oaicite:17]{index=17}
    pass

class ReducedDiagnostics(BaseModel):
    # reduced diagnostics placeholder
    pass


# ---------------------------------
# Collisions: static container + per-collision models
# ---------------------------------

class Collisions(BaseModel):
    collision_names: Optional[List[str]] = None

CollisionType = Literal[
    "Coulomb", "BackgroundMCC", "MonteCarlo", "BreitWheeler", "QuantumSynchrotron",
    "Compton", "BinaryCollision", "PairCreation",
    # keep permissive; list not exhaustive and varies by build
]

class Collision(BaseModel):
    type: Optional[CollisionType] = None
    species: Optional[List[str]] = None  # species involved, order depends on type
    # Add model-specific knobs as needed
    # See the collisions section. :contentReference[oaicite:18]{index=18}


# ---------------------------------
# PSATD & additional numerics (placeholders)
# ---------------------------------

class Psatd(BaseModel):
    # Add PSATD sub-options as needed (periodic_single_box_fft, etc.)
    periodic_single_box_fft: Optional[int] = None
    # The docs have an extensive PSATD section; fill incrementally. :contentReference[oaicite:19]{index=19}


# ---------------------------------
# Probes & in-situ vis (placeholders)
# ---------------------------------

class Probes(BaseModel):
    # e.g., probes in diagnostics; define when needed
    pass


# ---------------------------
# Root container for a deck
# ---------------------------

class Warpx(BaseModel):
    used_inputs_file: Optional[str] = None
    gamma_boost: Optional[float] = None
    boost_direction: Optional[Literal["x", "y", "z"]] = None
    zmax_plasma_to_compute_max_step: Optional[float] = None
    compute_max_step_from_btd: Optional[int] = None
    random_seed: Optional[str | int] = None
    grid_type: Optional[Literal["collocated", "staggered", "hybrid"]] = None

    B_ext_grid_init_style: Optional[Literal["constant", "parse_B_ext_grid_function", "read_from_file"]] = None
    E_ext_grid_init_style: Optional[Literal["constant", "parse_E_ext_grid_function", "read_from_file"]] = None
    B_external_grid: Optional[List[float]] = None
    E_external_grid: Optional[List[float]] = None
    Bx_external_grid_function: Optional[str] = None
    By_external_grid_function: Optional[str] = None
    Bz_external_grid_function: Optional[str] = None
    Ex_external_grid_function: Optional[str] = None
    Ey_external_grid_function: Optional[str] = None
    Ez_external_grid_function: Optional[str] = None
    read_fields_from_path: Optional[str] = None
    maxlevel_extEMfield_init: Optional[int] = None
    do_initial_div_cleaning: Optional[int] = None
    projection_div_cleaner_rtol: Optional[float] = None
    projection_div_cleaner_atol: Optional[float] = None
    use_hybrid_QED: Optional[bool] = None
    quantum_xi: Optional[float] = None

    numprocs: Optional[List[int]] = None
    do_dynamic_scheduling: Optional[bool] = None
    roundrobin_sfc: Optional[bool] = None
    split_high_density_boxes: Optional[bool] = None
    split_high_density_boxes_threshold: Optional[float] = None

class My_Constants(BaseModel):
    class Config:
        extra = "allow"  # accept any key/value


ALL_MODELS = [
    Misc,
    Amr,
    Geometry,
    Boundary,
    Pml,
    EmbeddedBoundary,
    Parallel,
    My_Constants,
    WarpxMovingWindow,
    Warpx,
    Algo,
    Macroscopic,
    HybridPICModel,
    ImplicitEvolve,
    Picard,
    Newton,
    ImplicitParticleSolve,
    Preconditioner,
    ImplicitConfig,
    Particles,
    Species,
    Lasers,
    Laser,
    ParticlesExternalFields,
    Diagnostics,
    FullDiagnostics,
    TimeAveragedDiagnostics,
    BackTransformedDiagnostics,
    ReducedDiagnostics,
    Collisions,
    Collision,
    Psatd,
    Probes,
]

MODEL_REGISTRY: Dict[str, Type[BaseModel]] = {cls.__name__.lower(): cls for cls in ALL_MODELS}

