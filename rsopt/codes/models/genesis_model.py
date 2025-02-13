"""Pydantic Models for Genesis1.3 v2 input files.
   Genesis does not actually use any substructure for the input file. The multiple classes are just for organization
   of this code.

   pydantic.FileType is not used for file names fields to allow for the possibility that the file may be created between
   when the model is first parsed and the simulation actually run. In some use cases other programs may produce
   supporting files during this period. So the file existence cannot be guaranteed.
"""
import typing
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

# Genesisv2 does not have separate commands so we define a name for consistency
GENESIS_COMMAND_NAME = 'newrun'

class _DefaultInteger19StringArray(Enum):
    RADIATION_POWER = 1
    LOG_DERIV_POWER_GROWTH = 1
    POWER_DENSITY_AXIS = 1
    RADIATION_PHASE_AXIS = 1
    TRANSVERSE_RAD_SIZE = 1
    RMS_DIFFRACTION_ANGLE = 0
    BEAM_ENERGY = 1
    BUNCHING_FACTOR = 1
    BEAM_SIZE_X = 1
    BEAM_SIZE_Y = 1
    ERROR_ENERGY_CONSERVATION = 1
    BEAM_POSITION_X = 0
    BEAM_POSITION_Y = 0
    ENERGY_SPREAD = 0
    ON_AXIS_FIELD_INTENSITY_FAR_FIELD = 0
    OUTPUT_2ND_HARMONIC = 0
    OUTPUT_3RD_HARMONIC = 0
    OUTPUT_4TH_HARMONIC = 0
    OUTPUT_5TH_HARMONIC = 0

    @classmethod
    def values_as_string(cls) -> str:
        """Returns a space-separated string of all enum values."""
        return " ".join(str(member.value) for member in cls.__members__.values())

class TaperModel(int, Enum):
    NOTAPER = 0
    LINEARTAPER = 1
    QUADRATICTAPER = 2

class Iscan(int, Enum):
    NONE = 0
    GAMMA0 = 1
    DELGAM = 2
    CURPEAK = 3
    XLAMDS = 4
    AW0 = 5
    ISEED = 6
    PXBEAM = 7
    PYBEAM = 8
    XBEAM = 9
    YBEAM = 10
    RXBEAM = 11
    RYBEAM = 12
    XLAMD = 13
    DELAW = 14
    ALPHAX = 15
    ALPHAY = 16
    EMITX = 17
    EMITY = 18
    PRAD0 = 19
    ZRAYL = 20
    ZWAIST = 21
    AWD = 22
    BEAMFILE = 23
    BEAMOPT = 24
    BEAMGAM = 25

class Iertyp(int, Enum):
    DISABLEFIELDERRORS = 0
    UNIFORM = 1
    UNIFORMCORRELATED = -1
    GAUSSIAN = 2
    GAUSSIANCORRELATED = -2

class Iwityp(int, Enum):
    PLANAR = 0
    HELICAL = 1

class Lbc(int, Enum):
    DIRICHLET = 0
    NEUMANN = 1

class IgamGaus(int, Enum):
    GAUSSIAN = 1
    UNIFORM = 2

class ItGaus(int, Enum):
    GAUSSIAN = 1
    UNIFORM = 2
    PARABOLIC = 3


class ElectronBeam(BaseModel):
    alphax: float = Field(0.0, description="ALPHAX, ALPHAY: Rotation of the transverse phase space distribution in x according to the standard definition ALPHAX = - < xx' >  GAMMA0 / EMITX.")
    alphay: float = Field(0.0, description="ALPHAY: Rotation of the transverse phase space distribution in y. See ALPHAX for more information.")
    bunch: float = Field(0.0, description="BUNCH: Initial value of the bunching factor, when quiet loading is used.")
    bunchphase: float = Field(0.0, description="BUNCHPHASE: Phase of initial bunching, when quiet loading is used.")
    conditx: float = Field(0.0, description="CONDITX, CONDITY: is the correlation strength between the amplitude of the electron's betatron oscillation and its energy. If the condition is applied correctly any emittance effects are removed from the FEL amplification and the focal strength can be increased. However it requires a conditioning beamline prior to the FEL to apply the correlation. Refer to the paper of Sessler(A.N. Sessler, et al., Phys. Rev. Lett 68 (1992) 309) for more information.")
    condity: float = Field(0.0, description="CONDITY: Same as CONDITX but for the correlation in the y-plane.")
    curpeak: float = Field(250.0, description="CURPEAK: Peak current of the electron beam. Time-independent simulations enforces a constant current.")
    cuttail: float = Field(-1.0, description="CUTTAIL: Cut in the transverse phase space in measures of the RMS size to collimate transverse beam tails/halos. The cut is applied after the loading and beam current is set accordingly to the reduced number of macro particles. It is disabled if the value is negative or the electron beam is imported from an external file.")
    delgam: float = Field(0.005, description="DELGAM: The RMS value of the energy distribution in terms of electron rest mass energy.")
    emitx: float = Field(2e-06, description="EMITX, EMITY: The normalized RMS emittance.")
    emity: float = Field(2e-06, description="EMITY: The normalized RMS emittance in y.")
    emod: float = Field(0.0, description="EMOD: Initial energy modulation, when quiet loading is used. The value is the modulation amplitude in terms of gamma.")
    emodphase: float = Field(0.0, description="EMODPHASE: Phase of initial energy modulation, when quiet loading is used.")
    gamma0: float = Field(35.2, description="GAMMA0: The mean energy of the electron beam in terms of the electron rest mass energy.")
    npart: int = Field(8192, description="NPART: The number of macro particles per slice. NPART must be a multiple of 4*NBINS and smaller than  defined in the source file 'genesis.def'.", ge=4, le=1000000)
    pxbeam: float = Field(0.0, description="PXBEAM, PYBEAM: Average normalized transverse momentum x of the electron beam at the undulator entrance. The momenta are defined as $\text{PXBEAM} = \beta_x\gamma$ where $\beta_x = cv_x$ is the average transverse velocity and $\gamma$ the Lorenz factor of the electron energy.")
    pybeam: float = Field(0.0, description="PYBEAM: Average normalized transverse momentum in y of the electron beam at the undulator entrance. See PXBEAM for more information.")
    rxbeam: float = Field(0.0001121, description="RXBEAM, RYBEAM: The RMS value of the transverse, spatial distribution.")
    rybeam: float = Field(0.0001121, description="RYBEAM: The RMS value in y of the transverse, spatial distribution.")
    xbeam: float = Field(0.0, description="XBEAM, YBEAM: Transverse position in $x$ of the electron beam at the undulator entrance with respect to the undulator axis.")
    ybeam: float = Field(0.0, description="YBEAM: Transverse position in y of the electron beam at the undulator entrance with respect to the undulator axis.")

class Focusing(BaseModel):
    dl: float = Field(0.0, description="DL: Length of the D-quadrupoles in measures of the undulator period.")
    drl: float = Field(0.0, description="DRL: Drift length between F and D quadrupoles in measures of undulator period.")
    f1st: float = Field(0.0, description="F1ST: Position within a FODO cell, where GENESIS 1.3 starts the FODO cell lattice. To start with a full F-quadrupole set F1ST to zero while a value of FL/2 begins the cell in the middle of the focusing quadrupole.")
    fl: float = Field(98.0, description="FL, DL: Length of the F-quadrupoles in measures of the undulator period. The integration step size DELZ must resolve the quadrupole length.")
    qfdx: float = Field(0.0, description="QFDX, QFDY: Maximum transverse misplacement of the quadrupoles in x-direction. A random offset between [-QFDX, QFDX] in x  is applied to every quadrupole. Quadrupole position errors are generated even if the magnetic field is defined by an external file.")
    qfdy: float = Field(0.0, description="QFDY: Maximum transverse misplacement of the quadrupoles in y-direction, respectively. See QFDX for more information.")
    quadd: float = Field(0.0, description="QUADD: The fields strength of D quadrupoles, defocusing in the x-plane. GENESIS 1.3 automatically applies the correct signs to QUADF and QUADD indicating the alternating focusing in the FODO-lattice.")
    quadf: float = Field(1.23, description="QUADF, QUADD: The field strength of F quadrupoles, focusing in the x-plane.")
    sl: float = Field(0.0, description="SL: Length of solenoid field in measures of undulator period. The solenoid is aligned to the beginning of each undulator section.")
    solen: float = Field(0.0, description="SOLEN: On-axis field strength of a superimposed solenoid field.")

class Io(BaseModel):
    alignradf: bool = Field(0, description="ALIGNRADF: When the FIELDFILE feature is used than Genesis 1.3 aligns the radiation field to the electron beam so that the radiaiton field is one full slippage behind the electron beam. In this case there is no unphysical calculation because the field which slips through the back into the first electron slice is fully defined. However this alignment depends on the undulator length. To disable the automatic alignment ALIGNRADF has to be set to a non-zero value. If this is the case the last slice of the radiaiton field is aligned with the last electron slice. Field slices, which slips into the first electron slice and which is not defined by the FIELDFILE is generated by the internal method of using the fundamental Gauss-Hermite mode")
    beamfile: str = Field('', description="BEAMFILE: Specifying a file containing a lookup table for the electron beam parameters at different position along the bunch. ")
    convharm: int = Field(1, description="CONVHARM: When the particle distribution is imported from a PARTFILE Genesis 1.3 allows the up-conversion to a higher harmonics. The harmonic number is specified with CONVHARM and has a default value of 1, corresponding to no up-conversion.The user has to make sure that in the input deck XLAMDS is adjusted, according to the new wavelength.")
    distfile: str = Field('', description="DISTFILE: If DISTFILE is defined, the 6d distribution is imported into GENESIS 1.3 and used to load the phase space. The quiet start algorithm is bypassed.")
    ffspec: int = Field(0, description="FFSPEC: To calculate a spectrum a post-processing step requires amplitude and phase, which are written to the output file, defined by LOUT of column 3 and 4. The values depend on the choice of FFSPEC. If the value is equal the near field on-axis intensity and phase is written, while for a negative value it is the same but in the far field zone. For a positive value the near field intensity is replaced by the total radiation power, assuming transverse coherence.")
    fieldfile: str = Field('', description="FIELDFILE: Defines the file containing the field distribution. The distribution is directly imported into the arrays, holding the field and the time-records. ")
    filetype: typing.Literal["ORIGINAL", "SDDS"] = Field("ORIGINAL", description="FILETYPE: Indication of the file type of all output files. ")
    ibfield: float = Field(0.0, description="IBFIELD: When the PARTFILE features is used the imported particle distribution can be tracked through a generic 4 magnet chicane before running the Genesis simulation. The chicane consists out of 4 bending magnets of the field strength IBFIELD and length IMAGL separated by 5 drifts of length IDRIL. If the field strength of the magnet is set to zero the feature of a chicane is disabled (default behavior)")
    idmpfld: bool = Field(0, description="IDMPFLD: Similar to IDUMP but only for the field distribution. ")
    idmppar: bool = Field(0, description="IDMPPAR: Similar to IDUMP but only for the particle distribution. ")
    idril: float = Field(0.0, description="IDRIL: The length of the 5 drift lengths of the magnetic chicane (three between the magnets and one before and after the magnets).")
    idump: bool = Field(0, description="IDUMP: If set to a non-zero value the complete particle and field distribution is dumped at the undulator exit into two output files. The filenames are the filename of the main output file plus the extension '.dpa' and '.dfl', respectively.")
    ilog: bool = Field(0, description="ILOG: If set to a non-zero value all further run-information and error messages are redirect to a log file. The name is the main output file name plus the extension '.log'.")
    imagl: float = Field(0.0, description="IMAGL: The length of each bending magnet of the chicane. If the magnet length is set to zero but IDRIL is not the resulting beam line correspond to a simple drift of the length 5 times IDRIL.")
    iotail: bool = Field(0, description="IOTAIL: If set to a non-zero value the output time window is the same as the simulated time window. Otherwise the output for the first slices covered by the slippage length is suppressed. Needed for bunches which are completely covered by the time-window.")
    iphsty: int = Field(1, description="IPHSTY: Generate output in the main output file at each IPHSTYth integration step. To disable output set IPHSTY to zero.")
    ippart: int = Field(0, description="IPPART: Write the particle distribution to file at each IPPARTth integration step. To disable output set IPPART to zero. The filename is the same of the main output file + the extension '.par'.")
    ipradi: int = Field(0, description="IPRADI: Write the field distribution to file at each IPRADIth integration step. To disable output set IPRADI to zero. The filename is the same of the main output file + the extension '.fld'.")
    ishsty: int = Field(1, description="ISHSTY: Generate output in the main output file for each ISHSTYth slice. ")
    ispart: int = Field(0, description="ISPART: Write the particle distribution to file for every ISPART slice. ")
    isradi: int = Field(0, description="ISRADI: Write the field distribution to file for every ISRADI slice.")
    itram11: float = Field(1.0, description="Define the matrix element for the transport matrix, which is applied when importing a particle distribution with the PARTFILE option. The matrix is defined in a standard way, acting on the vector (position in X, angle in X, position in Y, angle in Y, position in s, relative energy spread). The default value is the identity matrix.")
    itram12: float = Field(0.0, description="ITRAM12")
    itram13: float = Field(0.0, description="ITRAM13")
    itram14: float = Field(0.0, description="ITRAM14")
    itram15: float = Field(0.0, description="ITRAM15")
    itram16: float = Field(0.0, description="ITRAM16")
    itram21: float = Field(0.0, description="ITRAM21")
    itram22: float = Field(1.0, description="ITRAM22")
    itram23: float = Field(0.0, description="ITRAM23")
    itram24: float = Field(0.0, description="ITRAM24")
    itram25: float = Field(0.0, description="ITRAM25")
    itram26: float = Field(0.0, description="ITRAM26")
    itram31: float = Field(0.0, description="ITRAM31")
    itram32: float = Field(0.0, description="ITRAM32")
    itram33: float = Field(1.0, description="ITRAM33")
    itram34: float = Field(0.0, description="ITRAM34")
    itram35: float = Field(0.0, description="ITRAM35")
    itram36: float = Field(0.0, description="ITRAM36")
    itram41: float = Field(0.0, description="ITRAM41")
    itram42: float = Field(0.0, description="ITRAM42")
    itram43: float = Field(0.0, description="ITRAM43")
    itram44: float = Field(1.0, description="ITRAM44")
    itram45: float = Field(0.0, description="ITRAM45")
    itram46: float = Field(0.0, description="ITRAM46")
    itram51: float = Field(0.0, description="ITRAM51")
    itram52: float = Field(0.0, description="ITRAM52")
    itram53: float = Field(0.0, description="ITRAM53")
    itram54: float = Field(0.0, description="ITRAM54")
    itram55: float = Field(1.0, description="ITRAM55")
    itram56: float = Field(0.0, description="ITRAM56")
    itram61: float = Field(0.0, description="ITRAM61")
    itram62: float = Field(0.0, description="ITRAM62")
    itram63: float = Field(0.0, description="ITRAM63")
    itram64: float = Field(0.0, description="ITRAM64")
    itram65: float = Field(0.0, description="ITRAM65")
    itram66: float = Field(1.0, description="ITRAM66")
    lout: typing.GenericAlias(tuple, (int,)*19) = Field(default_factory=_DefaultInteger19StringArray.values_as_string, description="Defines, which parameter is included in the main output file.")
    maginfile: str = Field('', description="MAGINFILE Defines a file, which contains the magnetic field description, bypassing the interactive request of MAGIN.")
    magoutfile: str = Field('', description="Defines the file to which the magnetic field lattice is written to, bypassing the interactive request of MAGOUT.")
    multconv: int = Field(0, description="MULTCONV: If an imported particle distribution from a PARTFILE is up-converted to a higher harmonics the dault behavior is that the number of slices is preserved. This requires that ZSEP is adjusted together with XLAMDS. However if frequency resolution is a problem then a particle distribution can be converted and used multiple times to keep ZSEP constant.The disadvantage is that the CPU execution time is increased as well.")
    ndcut: int = Field(0, description="NDCUT: When loading a slice, only particles of the external distribution are used, which falls within a small time-window centered around the current position of the slice. If NDCUT has a value larger than zero the width is calculated by (tmax-tmin)/NDCUT, where tmax and tmin are determined, while scanning through the particle distribution. If NDCUT is zero, the time-window is adjusted, so that in average NPART/NBINS particles fall in each slice.")
    offsetradf: int = Field(0, description="OFFSETRADF: If the automatic alignment of the radiation field is disabled by setting ALIGNRADF to a non-zero value, the default alignment is that the first slice of the radiaiton field overlaps with the first slice of the electron beam. However the relative position can be controlled by OFFSETRADF. The value of OFFSETRADF defines the number of slice to skip before filling it for the first electron slice. E.g. a value of 4 will uses the 5th slice for the simulation of the first slice. slices one to 4 will be used to fill up the slippage field. If Genesis 1.3. require to fill a slice which is not defined by the FIELDFILE then it uses the internal method of a fundamental Gauss-Hermite mode.")
    outputfile: str = Field('', description="OUTPUTFILE: The name of the main output file. The prompt for the output filename at the beginning of a GENESIS 1.3 run will be suppressed.")
    partfile: str = Field('', description="PARTFILE: Defines the file containing the particle distribution. The distribution is directly imported into the arrays holding the particle variables. ")
    radfile: str = Field('', description="RADFILE: Specifying a file containing a lookup table for the seeding radiation pulse at different position along the bunch. ")
    trama: bool = Field(0, description="TRAMA: Non zero value enables that a transport matrix is applied to the electron distribution when importing it with PARTFILE. The individual matrix is defined by ITRAM##")

class ParticleLoading(BaseModel):
    iall: bool = Field(0, description="IALL: A non-zero value of IALL enforces that all slices are starting with the same element of the Hammersley sequences. It is recommend for time-dependent simulation excluding shot noise. IALL is set automatically for scans.")
    igamgaus: IgamGaus = Field(1, description="IGAMGAUS: Defines distribution profile in energy. A non-zero value generates a Gaussian distribution and a uniform otherwise.")
    ildgam: int = Field(5, description="ILDGAM: Hammersley base for loading the energy distribution. See ILDPSI for more information.Note that the loading of the energy distribution is Gaussian and uses two bases (ILDGAM and ILDGAM + 1).")
    ildpsi: int = Field(7, description="ILDPSI: Indices of the Hammersley sequence bases for loading the particle phase. GENESIS 1.3 uses the first 26 prime numbers as bases. To avoid correlation between the variables each base should be different. ")
    ildpx: int = Field(3, description="ILDPX, ILDPY: Hammersley base for loading the distribution in px. See ILDPSI for more information.")
    ildpy: int = Field(4, description="ILDPY: Hammersley base for loading the distribution in py. See ILDPSI for more information.")
    ildx: int = Field(1, description="ILDX, ILDY: Hammersley base for loading the distribution in x. See ILDPSI for more information.")
    ildy: int = Field(2, description="IDLY: Hammersley base for loading the distribution in y. See ILDPSI for more information.")
    inverfc: bool = Field(1, description="INVERFC: When set to a non-zero value, the inverted error function is used for generating a Gaussian distribution instead of the joint-probability method. It results in smoother distribution in energy and transverse dimensions.")
    ipseed: int = Field(-1, description="IPSEED: Initial seed for the random number generator used for particle phase fluctuation (shot noise). GENESIS 1.3 requires a re-initialization of the random number generator to guarantee the same loading whether magnetic field errors are used or not.")
    itgaus: ItGaus = Field(1, description="ITGAUS: Defines distribution profile in the transverse variables. The available distributions are:- Gaussian (ITGAUS=1)- Uniform (ITGAUS=2)- Parabolic (otherwise)")
    nbins: int = Field(4, description="NBINS: Number of bins in the particle phase. The value has to be at least 4 or larger than (2+2n), depending on whether the bunching at the nth harmonics is needed for space charge calculations or output.")

class Mesh(BaseModel):
    dgrid: float = Field(0.0, description="DGRID: Any value larger than zero explicitly sets the grid size, overruling the calculation by the RMAX0-parameter.")
    iscrkup: bool = Field(0, description="ISCRKUP: If set to a non-zero value then the space charge field is updated at each of the 4 Runge-Kutta integration steps instead of the default behavior, where the space charge field is calculated only once before the Runge-Kutta integration. It increases the stability and precision of the space charge field but it comes with a cost in slower execution speed.")
    lbc: Lbc = Field(0, description="LBC: Flag to set the boundary condition for the field solver. The options are Dirichlet boundary condition (LBC = 0) and Neumann boundary condition (otherwise). The grid should be chosen large enough so that the choice of LBC should not change the results.")
    ncar: int = Field(151, description="NCAR: The number of grid points for the radiation field along a single axis. The total number for the mesh is NCAR2. NCAR must be an odd number to cover the undulator axis with one grid point. Do not exceed NCMAX defined in the source file 'genesis.def'.")
    nptr: int = Field(40, description="NPTR: Number of radial grid points, on which the space charge field is evaluated. The radial axis is automatically chosen by GENESIS 1.3 to be twice as long as the maximum offset of macro particles relative to the center of the electron beam. This excludes effects of the boundary condition even for the case of narrow beams.")
    nscr: int = Field(1, description="NSCR: Number of azimuthal modes for space charge calculation.")
    nscz: int = Field(1, description="NSCZ: Number of longitudinal Fourier components for space charge calculation. NSCZ must be greater than 0 to include space charge but less than (2NBINS+2) for valid results.")
    rmax0: float = Field(9.0, description="RMAX0: GENESIS 1.3 estimates the size of the grid on which the radiation field is discretized by scaling the averages size of the initial radiation field and beam size with RMAX0. The explicit size is [-DGRID,DGRID] in both dimensions with $\text{DGRID} = \text{RMAX0}(\sigma_{r,beam}+\sigma_{r,field})$.The electron beam size is the RMS sum of RXBEAM and RYBEAM while the radiation field  size is calculated with ZRAYL and ZWAIST.")
    rmax0sc: float = Field(0.0, description="RMAX0SC: Explicitly defines the radial grid size for space charge calculations when set to a positive value. Otherwise, Genesis calculates the grid size from the current size of the electron beam.")

class Radiation(BaseModel):
    iallharm: bool = Field(0, description="IALLHARM: As a default setting only the fundamental and the harmonic, defined by NHARM are calculated. Setting the value to a non-zero value will also include all harmonics between. This option will be set automatically when the harmonics are calculated self-consistently.")
    iharmsc: bool = Field(0, description="IHARMSC: Typically the harmonics are driven by the non-linear dynamics on the fundamental and the feed back of the harmonics on the electron beam can be neglected for the sake of faster calculation. However setting IHARMSC to a non-zero value includes the coupling of the harmonic radiation back to the electron beam for a self-consistent model of harmonics. Enabling this feature will automatically include all harmonics by setting IALLHARM to one.")
    nharm: int = Field(1, description="NHARM: Enables the calculation of harmonics up to the one, specified by NHARM. Note that the number of NBINS has to be at least twice as large as NHARM to allow for the correct representation of the harmonics. Note also that this parameter does not enable automatically the output. For that the corresponding bit in LOUT has to be set as well.")
    prad0: float = Field(10.0, description="PRAD0: The input power of the radiation field. For SASE simulation PRAD0 should be set to zero value or at least well below the shot noise level.")
    pradh0: float = Field(0.0, description="Radiation power for seeding with a harmonics, defined by NHARM.The waist position and waist size is identical to the fundamental (ZWAIST) thus using a scaled value of NHARM*ZRAYL for the Rayleigh length.")
    xlamds: float = Field(1.2852e-05, description="XLAMDS: The resonant radiation wavelength. Due to the bandwidth of time-dependent simulation SASE simulations do not require a very precise value for XLAMDS.")
    zrayl: float = Field(0.5, description="ZRAYL: The Rayleigh length of the seeding radiation field. ZRAYL is defined as pi*w0^2/XLAMDS where w0 is the radius of the optical beam waist. The Rayleigh length is a measure for the diffraction w(z)^2 = w0^2(1 + (z - ZWAIST)^2/ZRAYL^2) and is needed to calculate the size and divergence/convergence of the seeding field at the undulator entrance. Because the field size can determine the grid size it is strongly recommended to supply reasonable numbers for ZRAYL and ZWAIST even for simulation starting from noise.")
    zwaist: float = Field(0.0, description="ZWAIST: Position of the waist of the seeding radiation field with respect to the undulator entrance. ZWAIST is needed in combination with ZRAYL to calculate the initial radiation field. Note that a waist position within the undulator (ZWAIST  >  0) is only used to determine the initial convergence. The FEL interaction might significantly change the beam size and diffraction of the radiation field (gain guiding).")

class Scan(BaseModel):
    iscan: Iscan = Field(0, description="ISCAN: Selects the parameter for a scan over a certain range of its value. The last two enables a user-defined scan, where a steady-state run is performed for each entry of the supplied BEAMFILE. BEAMOPT differs from BEAMFILE that it automatically adjust XLAMDS according to the resonance condition and the beam energy, defined in the BEAMFILE.The BEAMGAM option is similar to BEAMFILE, but overwrites the value of energy with GAMMA0 from the main input file.")
    nscan: int = Field(3, description="NSCAN: Number of steps per scan.")
    svar: float = Field(0.01, description="SVAR: Defines the scan range of the selected scan parameter. The parameter is varied between (1-SVAR) and (1+SVAR) of its initial value. One exception is the scan over ISEED where the random number generator is not reinitialized.")

class SimulationControl(BaseModel):
    delz: float = Field(1.0, description="DELZ: Integration step size in measure of the undulator period length.")
    eloss: float = Field(0.0, description="ELOSS: Externally applied energy loss of the electron beam.")
    iorb: bool = Field(0, description="IORB: Flag for orbit correction. For any non-zero value the offset due to the wiggle motion is taken into account for the interaction between electron beam and radiation field. The correction is not included in the output values for the beam centroid position.")
    isravg: bool = Field(0, description="ISRAVG: If set to a non-zero value the energy loss due to spontaneous synchrotron radiation is included in the calculation.")
    isrsig: bool = Field(0, description="ISRSIG: If set to a non-zero value the increase of the energy spread due to the quantum fluctuation of the spontaneous synchrotron radiation is included in the calculation.")
    version: float = Field(0.1, description="Used for backward compatibility of the input decks. Some parameters might change their behavior for older versions of GENESIS 1.3. The current version is 1.0.")
    zstop: float = Field(0.0, description="ZSTOP: Defines the total integration length. If the undulator length is shorter than ZSTOP or ZSTOP is zero or negative, the parameter is ignored and the integration is performed over the entire undulator.")

class TimeDependence(BaseModel):
    curlen: float = Field(0.001, description="CURLEN: Bunch length of the current profile. If CURLEN is positive a Gaussian distribution is generated with an RMS length given by CURLEN. A negative or zero value yield a constant profile.")
    isntyp: bool = Field(0, description="ISNTYP: For VERSION below 1.0 only the Pennman algorithm is used for the shot noise, which is only correct for the fundamental wavelength, but for a higher version the default is the Fawley algorithm which applies also the correct shotnoise to all higher harmonics. If the user wants to use the Pennman algorithm at a higher version number (which is not recommended), the value of ISNTYP has to be set to a non-zero value.")
    itdp: bool = Field(0, description="ITDP: A non-zero value enables time-dependent simulation. Time-dependence is not allowed if the scan-feature is enabled. ")
    nslice: int = Field(408, description="NSLICE: Total number of simulated slices. It defines the time window of the simulation with NSLICE * ZSEP * XLAMDS/c. Note that the output does not start with the first slice unless the parameter IOTAIL is set. If NSLICE set to zero it automatically adjust NSLICE and NTAIL to the time-window given by the external input files (BEAMFILE or DISTFILE). It assumes 6 standard deviation for a Gaussian distribution or the absolute value of CURLEN for a step profile.")
    ntail: int = Field(-253, description="NTAIL: Position of the first simulated slice in measures of ZSEP*XLAMDS. GENESIS 1.3 starts with the tail side of the time window, progressing towards the head.  Thus a negative or positive value shifts the slices towards the tail or head region of the beam, respectively. For a constant profile (CURLEN  <  0) NTAIL has no impact.")
    shotnoise: float = Field(1.0, description="SHOTNOISE: GENESIS 1.3 applies a random offset to each macro particle phase to generate the correct statistic for the bunching factor. Each offset is scaled prior by SHOTNOISE, thus SHOTNOISE can be set to zero to disable shot noise. ")
    zsep: float = Field(1.0, description="ZSEP: Separation of beam slices in measures of the radiation wavelength. ZSEP must be a multiple of DELZ.")

class Undulator(BaseModel):
    aw0: float = Field(0.735, description="AW0: The normalized, dimensionless RMS undulator parameter, defined by $\text{AW0} = (e/mc)(B_u/k_u)$, where e is the electron charge, $m$ is electron mass, $c$ is speed of light, $k_u=2\pi/\lambda_u$ is the undulator wave number, $\lambda_u$ is the undulator period. $B_u$ is the RMS undulator field with $B_u = B_\rho/2$ for a planar undulator and $B_u = B_\rho$ for a helical undulator, where $B_\rho$ is the on-axis peak field.")
    awd: float = Field(0.735, description="AWD: A virtual undulator parameter for the gap between undulator modules. The only purpose of this parameter is to delay the longitudinal motion of the electrons in the same manner as AW0 does within the undulator modules. It is used to keep the electron and radiation phases synchronize up to the point when the interaction at the next undulator module starts again. AWD has typically the same value as AW0, but might vary for optimum matching between the modules. ")
    awx: float = Field(0.0, description="AWX, AWY: Maximum offset in x for undulator module misalignment. The error for each individual module follows a uniform distribution")
    awy: float = Field(0.0, description="AWY: Maximum offset in y for undulator module misalignment. The error for each individual module follows a uniform distribution")
    delaw: float = Field(0.0, description="DELAW: RMS value of the undulator field error distribution. A value of zero disables field errors.")
    fbess0: float = Field(0.0, description="FBESS0: The coupling factor of the electron beam to the radiation field due to the longitudinal wiggle motion of the electrons.  It is 1.0 for a helical undulator and $J_0(x) - J_1(x)$ for a planar undulator where $J_0(x), J_1(x)$ are Bessel functions and $x = \text{AW0}^2/2(1+\text{AW0}^2)$. If FBESS0 is set to 0.0 GENESIS 1.3 calculates the value.")
    iertyp: Iertyp = Field(0, description="IERTYP: Type of undulator field errors. Either a uniform (+/-1) or Gaussian (+/- 2) distribution can be chosen. If IERTYP is negative the errors are correlated to minimize the first and second field integral. IERTYP =0 disables field errors. Field errors requires a integration step size of half an undulator period (DELZ = 0.5). Note that field errors are applied even if the magnetic lattice is defined by an external file.")
    iseed: int = Field(-1, description="ISEED: The initial seeding of the random number generator for field errors.")
    iwityp: Iwityp = Field(0, description="IWITYP: Flag indicating the undulator type. Planar undulator or helical.")
    nsec: int = Field(1, description="NSEC: The number of sections of the undulator. Note that a section length in not automatically identical with the undulator module length. GENESIS 1.3 aligns modules to the FODO-lattice. If a module ends within a FODO cell the next module starts with the beginning of the next cell. Sometimes this results in a longitudinal gap between adjacent undulator modules.")
    nwig: int = Field(98, description="NWIG: The number of periods within a single undulator module. The product of NWIG and XLAMD defines the length of the undulator module.")
    wcoefz1: float = Field(0.0, description="WCOEFZ(1): Start of undulator tapering. Note that tapering is applied, even the magnetic lattice is defined by an external file.")
    wcoefz2: float = Field(0.0, description="WCOEFZ(2): The relative change of the undulator field over the entire taper length (AW(exit) = (1 - WCOEFZ(2)) AW(entrance)). In the case of a multi section undulator GENESIS 1.3 tapers the magnetic field over the gaps as well, resulting in a jump of the magnetic field AW(z) between two modules.")
    wcoefz3: TaperModel = Field(0, description="WCOEFZ(3): The taper model:= 1 for linear taper,= 2 for quadratic taper, or no taper otherwise.")
    xkx: float = Field(0.0, description="XKX, XKY: Normalized natural focusing of the undulator in $x$. Common values are XKX = 0.0, XKY = 1.0 for a planar undulator or XKX, XKY = 0.5 for a helical undulator, but might vary if focusing by curved pole faces is simulated. The values should fulfill the constraint XKX + XKY = 1.0. ")
    xky: float = Field(1.0, description="XKY: Normalized natural focusing of the undulator in x. See XKX for more information.")
    xlamd: float = Field(0.0205, description="XLAMD: The undulator period length.")

    @model_validator(mode='before')
    @classmethod
    def disperse_wcoefz(cls, data: dict) -> dict:
        if data.get('wcoefz'):
            assert len(data['wcoefz']) == 3, (f"field wcoefz is missing data. "
                                              f"Expected 3 values, received {data['wcoefz']}")
            data['wcoefz1'], data['wcoefz2'], data['wcoefz3'] = data['wcoefz']
        return data

class Genesis(ElectronBeam, Focusing, Io, ParticleLoading, Mesh, Radiation,
              Scan, SimulationControl, TimeDependence, Undulator):
    command_name: typing.Literal[GENESIS_COMMAND_NAME] = Field(GENESIS_COMMAND_NAME, exclude=True)

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        formatted_data = {}
        for k, v in data.items():
            if isinstance(v, bool):
                formatted_data[k] = int(v)
            elif isinstance(v, str):
                formatted_data[k] = "\"{}\"".format(v)
            else:
                formatted_data[k] = v
        return formatted_data

# Defined for consistency with other models that have many commands - Union of a single type just returns the type though
GENESIS = typing.Union[Genesis]