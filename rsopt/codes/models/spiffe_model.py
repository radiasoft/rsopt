import enum
import typing

from pydantic import BaseModel, Field
from typing import Optional, Literal
from pydantic.functional_validators import AfterValidator, BeforeValidator
from typing_extensions import Annotated

def strip_quotes(v: str) -> str:
    return v.strip("'\"")

def add_double_quotes(v: str) -> str:
    return f"\"{v}\""

class DefineGeometryParams(BaseModel):
    command_name: Literal['define_geometry'] = Field("define_geometry", exclude=True)

    nz: Optional[int] = Field(0, description="Number of grid lines in the z dimension.")
    nr: Optional[int] = Field(0, description="Number of grid lines in the r dimension.")
    zmin: Optional[float] = Field(0.0, description="Starting longitudinal coordinate.")
    zmax: Optional[float] = Field(0.0, description="Ending longitudinal coordinate.")
    rmax: Optional[float] = Field(0.0, description="Maximum radial coordinate.")
    zr_factor: Optional[float] = Field(1,
                                       description="Factor to multiply z and r values in the boundary input file to convert to meters.")
    rootname: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None, description="Rootname for output filenames. Defaults to input file rootname.")
    boundary: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None,
                                    description="Name of input file containing cavity boundary and surface potentials.")
    boundary_output: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None,
                                           description="Output file for SDDS data of the ideal boundary coordinates.")
    # There is a line here: "STRING urmel_boundary_output = NULL;"" not mentioned in details. Is it a typo?
    discrete_boundary_output: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None,
                                                    description="Output file for SDDS data of the actual boundary coordinates.")
    interior_points: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None,
                                           description="Output file for SDDS data of all interior points of the cavity.")
    lower: Optional[Annotated[Literal["Dirichlet", "Neumann"], BeforeValidator(strip_quotes)]] = Field("Dirichlet",
                                                                                                      description="Boundary condition for the lower edge.")
    upper: Optional[Annotated[Literal["Dirichlet", "Neumann"], BeforeValidator(strip_quotes)]] = Field("Neumann",
                                                                                                      description="Boundary condition for the upper edge.")
    right: Optional[Annotated[Literal["Dirichlet", "Neumann"], BeforeValidator(strip_quotes)]] = Field("Neumann",
                                                                                                      description="Boundary condition for the right edge.")
    left: Optional[Annotated[Literal["Dirichlet", "Neumann"], BeforeValidator(strip_quotes)]] = Field("Neumann",
                                                                                                     description="Boundary condition for the left edge.")
    include_TE_fields: Optional[int] = Field(0, description="Flag to include transverse-electric fields.")
    exclude_TM_fields: Optional[int] = Field(0, description="Flag to exclude transverse-magnetic fields.")
    turn_off_Er: Optional[int] = Field(0, description="Flag to turn off radial electric field.")
    turn_off_Ez: Optional[int] = Field(0, description="Flag to turn off longitudinal electric field.")
    turn_off_Ephi: Optional[int] = Field(0, description="Flag to turn off azimuthal electric field.")
    turn_off_Br: Optional[int] = Field(0, description="Flag to turn off radial magnetic field.")
    turn_off_Bz: Optional[int] = Field(0, description="Flag to turn off longitudinal magnetic field.")
    turn_off_Bphi: Optional[int] = Field(0, description="Flag to turn off azimuthal magnetic field.")
    print_grids: Optional[int] = Field(0, description="Flag to print a text-based picture of the simulation grids.")
    radial_interpolation: Optional[int] = Field(1, description="Flag to enable radial field interpolation.")
    longitudinal_interpolation: Optional[int] = Field(1, description="Flag to enable longitudinal field interpolation.")
    radial_smearing: Optional[int] = Field(0, description="Flag to enable radial smearing of charge and current.")
    longitudinal_smearing: Optional[int] = Field(0,
                                                 description="Flag to enable longitudinal smearing of charge and current.")


class GeometryPoint(BaseModel):
    command_name: Literal['geometry'] = Field("geometry", exclude=True)

    nt: Optional[int] = 1
    x: float = 0.0
    y: float = 0.0
    x0: Optional[float] = 0.0
    y0: Optional[float] = 0.0
    r: Optional[float] = 0.0
    theta: Optional[float] = 0.0
    potential: Optional[float] = 0.0


class DefineAntennaParams(BaseModel):
    command_name: Literal['define_antenna'] = Field("define_antenna", exclude=True)

    start: Optional[float] = Field(0.0, description="Starting position of the antenna in the defined direction.")
    end: Optional[float] = Field(0.0, description="Ending position of the antenna in the defined direction.")
    position: Optional[float] = Field(0.0,
                                      description="Position of the antenna in the 'other' direction (perpendicular to 'direction').")
    direction: Optional[Annotated[Literal["z", "r"], BeforeValidator(strip_quotes)]] = Field("z",
                                                                                            description="Direction of the antenna, either longitudinal ('z') or radial ('r').")
    current: Optional[float] = Field(0.0, description="Current in amperes driving the antenna.")
    frequency: Optional[float] = Field(0.0, description="Frequency in hertz of the antenna.")
    phase: Optional[float] = Field(0.0, description="Phase of the antenna drive in radians.")
    waveform: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None,
                                    description="File containing the envelope function for the antenna drive. The file must contain 't' for time and 'W' for envelope.")
    time_offset: Optional[float] = Field(0.0, description="Time offset for the antenna waveform.")


class LoadFieldsParams(BaseModel):
    command_name: Literal['load_fields'] = Field("load_fields", exclude=True)

    filename: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = None
    Ez_peak: Optional[float] = 0.0
    factor: Optional[float] = 1.0
    time_threshold: Optional[float] = 0.0
    overlay: Optional[int] = 0


class SetConstantFieldsParams(BaseModel):
    command_name: Literal['set_constant_fields'] = Field("set_constant_fields", exclude=True)

    Ez: Optional[float] = 0.0
    Er: Optional[float] = 0.0
    Ephi: Optional[float] = 0.0
    Bz: Optional[float] = 0.0
    Br: Optional[float] = 0.0
    Bphi: Optional[float] = 0.0


class AddOnAxisFieldsParams(BaseModel):
    command_name: Literal['add_on_axis_fields'] = Field("add_on_axis_fields", exclude=True)

    filename: str
    z_name: str
    Ez_name: str
    Ez_peak: Optional[float] = 0.0
    frequency: Optional[float] = 0.0
    z_offset: Optional[float] = 0.0
    expansion_order: Optional[Literal[0, 1, 2, 3]] = 3
    fields_used: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = None


class DefineSolenoidParams(BaseModel):
    command_name: Literal['define_solenoid'] = Field("define_solenoid", exclude=True)

    radius: Optional[float] = Field(0.0, description="The radius of the coils in meters.")
    evaluation_radius_limit: Optional[float] = Field(0.0,
                                                     description="The maximum radius in meters at which the solenoidal fields should be computed.")
    z_start: Optional[float] = Field(0.0, description="The starting longitudinal coordinate of the coils, in meters.")
    z_end: Optional[float] = Field(0.0, description="The ending longitudinal coordinate of the coils, in meters.")
    current: Optional[float] = Field(0.0, description="The current in each coil in Amperes.")
    Bz_peak: Optional[float] = Field(0.0,
                                     description="The peak on-axis longitudinal magnetic field in Tesla desired from this solenoid.")
    turns: Optional[int] = Field(1, description="The number of turns (or coils) in the solenoid.")
    symmetry: Optional[int] = Field(0,
                                    description="Symmetry of the solenoid: 0 for no symmetry, 1 for even symmetry, -1 for odd symmetry.")
    field_output: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None, description="Request output of the solenoid field to an SDDS file.")
    bucking: Optional[int] = Field(0,
                                   description="Flag for bucking solenoid. Adjusts current to zero the on-axis value of Bz.")
    z_buck: Optional[float] = Field(0.0,
                                    description="The location at which the field is bucked, if bucking is enabled.")


class DefineCathodeParams(BaseModel):
    command_name: Literal['define_cathode'] = Field("define_cathode", exclude=True)

    z_position: Optional[float] = Field(0.0, description="Longitudinal position of the cathode in meters.")
    inner_radius: Optional[float] = Field(0.0, description="Inner radius of the cathode in meters.")
    outer_radius: Optional[float] = Field(0.0, description="Outer radius of the cathode in meters.")
    current_density: Optional[float] = Field(0.0, description="Base current density in Amperes per square meter.")
    temperature: Optional[float] = Field(0.0,
                                         description="Temperature of the cathode in Kelvin. A zero value indicates constant emission.")
    work_function: Optional[float] = Field(0.0,
                                           description="Work function of the cathode material in eV. Must be nonzero if temperature is nonzero.")
    field_emission: Optional[int] = Field(0,
                                          description="Flag for field emission mode (nonzero indicates field emission).")
    field_emission_beta: Optional[float] = Field(1,
                                                 description="Field enhancement factor for field emission calculations.")
    electrons_per_macroparticle: Optional[float] = Field(0.0,
                                                         description="Number of electrons represented by each macroparticle.")
    number_per_step: Optional[float] = Field(0.0,
                                             description="How many macroparticles to emit per step. Incompatible with electrons_per_macroparticle.")
    start_time: Optional[float] = Field(0.0, description="Start time for emission in seconds.")
    stop_time: Optional[float] = Field(0.0, description="Stop time for emission in seconds.")
    autophase: Optional[int] = Field(0, description="Flag to enable autophase emission, starting when field is proper.")
    time_offset: Optional[float] = Field(0.0, description="Time offset for autophase emission relative to start time.")
    initial_pz: Optional[float] = Field(0.0,
                                        description="Initial longitudinal momentum of emitted particles (normalized).")
    initial_omega: Optional[float] = Field(0.0,
                                           description="Initial angular velocity of particles in radians per second.")
    stiffness: Optional[float] = Field(1.0, description="Beam stiffness, in electron masses.")
    discretize_radii: Optional[int] = Field(0, description="Flag to discretize emission radii.")
    random_number_seed: Optional[int] = Field(987654321,
                                              description="Seed for the particle emission random number generator.")
    distribution_correction_interval: Optional[int] = Field(0,
                                                            description="Interval for correcting emitted particle distribution.")
    spread_over_dt: Optional[int] = Field(0, description="Flag to spread emitted particles over time step.")
    zoned_emission: Optional[int] = Field(1, description="Flag to perform emission by annular zones.")
    halton_radix_t: Optional[int] = Field(0, description="Halton radix for time values.")
    halton_radix_r: Optional[int] = Field(0, description="Halton radix for radius values.")
    profile: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None, description="Name of SDDS-protocol file for time-profile modulation.")
    profile_factor_name: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None, description="Column name for current-density adjustment factor.")
    profile_time_name: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None,
                                             description="Column name for corresponding time of adjustment factor.")


class LoadParticlesParams(BaseModel):
    command_name: Literal['load_particles'] = Field("load_particles", exclude=True)

    filename: str
    sample_interval: Optional[int] = 1
    stiffness: Optional[float] = 1.0


class PoissonCorrectionParams(BaseModel):
    command_name: Literal['poisson_correction'] = Field("poisson_correction", exclude=True)

    start_time: Optional[float] = 0.0
    step_interval: Optional[int] = 0
    accuracy: Optional[float] = 1e-6
    error_charge_threshold: Optional[float] = 0.0
    maximum_iterations: Optional[int] = 1000
    verbosity: Optional[int] = 0
    test_charge: Optional[float] = 0.0
    z_test_charge: Optional[float] = 0.0
    r_test_charge: Optional[float] = 0.0
    guess_type: Optional[Annotated[Literal["none", "uniform", "gaussian"], BeforeValidator(strip_quotes)]] = "none"


class DefineScreenParams(BaseModel):
    command_name: Literal['define_screen'] = Field("define_screen", exclude=True)

    filename: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = None
    template: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = None
    z_position: Optional[float] = 0.0
    delta_z: Optional[float] = 0.0
    number_of_screens: Optional[int] = 1
    start_time: Optional[float] = 0.0
    direction: Optional[Annotated[Literal["forward", "backward"], BeforeValidator(strip_quotes)]] = "forward"


class DefineSecondaryEmissionParams(BaseModel):
    command_name: Literal['define_secondary_emission'] = Field("define_secondary_emission", exclude=True)

    input_file: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = None
    kinetic_energy_column: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = None
    yield_column: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = None
    yield_limit: Optional[int] = 0
    emitted_momentum: Optional[float] = 0.0
    verbosity: Optional[int] = 0


class DefineSnapshotsParams(BaseModel):
    command_name: Literal['define_snapshots'] = Field("define_snapshots", exclude=True)

    filename: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = None
    time_interval: Optional[float] = 0.0
    start_time: Optional[float] = 0.0


class DefineFieldOutputParams(BaseModel):
    command_name: Literal['define_field_output'] = Field("define_field_output", exclude=True)

    filename: str
    time_interval: Optional[float] = 0.0
    start_time: Optional[float] = 0.0
    z_interval: Optional[int] = 1
    r_interval: Optional[int] = 1
    exclude_imposed_field: Optional[int] = 0
    separate_imposed_field: Optional[int] = 0


class DefineFieldSavingParams(BaseModel):
    command_name: Literal['define_field_saving'] = Field("define_field_saving", exclude=True)

    filename: str
    time_interval: Optional[float] = 0.0
    start_time: Optional[float] = 0.0
    save_before_exiting: Optional[int] = 0


class DefineFieldSamplingParams(BaseModel):
    command_name: Literal['define_field_sampling'] = Field("define_field_sampling", exclude=True)

    filename: str
    component: Annotated[
        Literal["Ez", "Er", "Jz", "Jr", "Bphi", "Phi", "Ephi", "Bz", "Br", "Q"], BeforeValidator(strip_quotes)]
    direction: Annotated[Literal["z", "r"], BeforeValidator(strip_quotes)]
    min_coord: Optional[float] = 0.0
    max_coord: Optional[float] = 0.0
    position: Optional[float] = 0.0
    time_interval: Optional[float] = 0.0
    start_time: Optional[float] = 0.0
    time_sequence: Optional[int] = 0


class IntegrateParams(BaseModel):
    command_name: Literal['integrate'] = Field("integrate", exclude=True)

    dt_integration: Optional[float] = Field(0.0, description="Simulation step size in seconds.")
    start_time: Optional[float] = Field(0.0,
                                        description="Simulation start time. Typically 0 for new runs. Ignored for runs that involve fields loaded from other simulations.")
    finish_time: Optional[float] = Field(0.0, description="Simulation stop time.")
    status_interval: Optional[int] = Field(-1,
                                           description="Interval in units of a simulation step between status printouts.")
    space_charge: Optional[int] = Field(0, description="Flag requesting inclusion of space-charge in the simulation.")
    check_divergence: Optional[int] = Field(0,
                                            description="Flag requesting that status printouts include a check of the field values using the divergence equation.")
    smoothing_parameter: Optional[float] = Field(0.0,
                                                 description="Specifies a simple spatial filter for the current density. Rarely used and not recommended.")
    J_filter_multiplier: Optional[float] = Field(0.0,
                                                 description="Specifies a simple time-domain filter for the current density. Rarely used and not recommended.")
    terminate_on_total_loss: Optional[int] = Field(0,
                                                   description="Flag requesting that when all simulation particles are lost, the simulation should terminate.")
    status_output: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None,
                                         description="Provide the name of a file to which to write status information, including statistics on the beams and fields. File is in SDDS format.")
    lost_particles: Optional[Annotated[str, AfterValidator(add_double_quotes)]] = Field(None,
                                          description="Provide the name of a file to which to write information about particles that get lost. File is in SDDS format.")

SPIFFE = typing.Union[
    DefineGeometryParams,
    DefineAntennaParams,
    LoadFieldsParams,
    SetConstantFieldsParams,
    AddOnAxisFieldsParams,
    DefineSolenoidParams,
    DefineCathodeParams,
    LoadParticlesParams,
    PoissonCorrectionParams,
    DefineScreenParams,
    DefineSecondaryEmissionParams,
    DefineSnapshotsParams,
    DefineFieldOutputParams,
    DefineFieldSamplingParams,
    DefineFieldSavingParams,
    DefineFieldSamplingParams,
    IntegrateParams
]

