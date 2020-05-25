import sys, os
from rswarp.run_files.tec.gridded_tec_3d import main
from rswarp.run_files.tec.tec_utilities import read_parameter_file


def simulate_efficiency(attribute_file, run_id=None):
    """
    x_struts: Number of struts that intercept the x-axis.
    y_struts: Number of struts that intercept the y-axis
    V_grid: Voltage to place on the grid in Volts.
    gap_distance: Distance from the emitter to the collector in meters
    grid_height: Distance from the emitter to the grid normalized by gap distance.
    strut_width: Transverse extent of the struts in meters.
    strut_height: Longitudinal extent of the struts in meters.
    T_em: Temperature of emitter in Kelvin
    phi_em: Reistivity of the emitter side wiring in ohm*cm
    T_coll: Temperature of collector in Kelvin
    phi_cw: Resistivity of collector side wiring in ohm*cm
    run_id: Run id will be added to diagnostic folder name. Mainly used for parallel optimization.
    """
    print("trying to open file", attribute_file)
    print("I am in", os.getcwd())
    run_attributes = read_parameter_file(attribute_file)
    if not run_id:
        run_id = os.path.split(attribute_file)[-1]
        run_id = os.path.splitext(run_id)[0]
        run_attributes['run_id'] = '{}'.format('_' + run_id)
    else:
        run_attributes['run_id'] = run_id

    main(**run_attributes)
