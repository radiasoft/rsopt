import radia as rad
import numpy as np
from scipy.constants import mu_0, e, m_e, c


def hybrid_undulator(lpx, lpy, lpz, pole_properties, pole_segmentation, pole_color,
                     lmx, lmz, magnet_properties, magnet_segmentation, magnet_color,
                     gap, offset, period, period_number):
    """
    create hybrid undulator magnet
    arguments:
      pole_dimensions = [lpx, lpy, lpz] = dimensions of the iron poles / mm
      pole_properties = magnetic properties of the iron poles (M-H curve)
      pole_separation = segmentation of the iron poles
      pole_color = [r,g,b] = color for the iron poles
      magnet_dimensions = [lmx, lmy, lmz] = dimensions of the magnet blocks / mm
      magnet_properties = magnetic properties of the magnet blocks (remanent magnetization)
      magnet_segmentation = segmentation of the magnet blocks
      magnet_color = [r,g,b] = color for the magnet blocks
      gap = undulator gap / mm
      offset = vertical offset / mm of the magnet blocks w/rt the poles
      period = length of one undulator period / mm
      period_number = number of full periods of the undulator magnetic field
    return: Radia representations of
      undulator group, poles, permanent magnets
    """
    period_number = int(period_number)
    pole_dimensions = [lpx, lpy, lpz]
    lmy = period / 2. - pole_dimensions[1]
    magnet_dimensions = [lmx, lmy, lmz]
    zer = [0, 0, 0]
    # full magnet will be assembled into this Radia group
    grp = rad.ObjCnt([])
    # principal poles and magnet blocks in octant(+,+,–)
    # -- half pole
    y = pole_dimensions[1] / 4
    pole = rad.ObjFullMag([pole_dimensions[0] / 4, y, -pole_dimensions[2] / 2 - gap / 2],
                          [pole_dimensions[0] / 2, pole_dimensions[1] / 2, pole_dimensions[2]],
                          zer, pole_segmentation, grp, pole_properties, pole_color)
    y += pole_dimensions[1] / 4
    # -- magnet and pole pairs
    magnetization_dir = -1
    for i in range(0, period_number):
        init_magnetization = [0, magnetization_dir, 0]
        magnetization_dir *= -1
        y += magnet_dimensions[1] / 2
        magnet = rad.ObjFullMag([magnet_dimensions[0] / 4, y, -magnet_dimensions[2] / 2 - gap / 2 - offset],
                                [magnet_dimensions[0] / 2, magnet_dimensions[1], magnet_dimensions[2]],
                                init_magnetization, magnet_segmentation, grp, magnet_properties, magnet_color)
        y += (magnet_dimensions[1] + pole_dimensions[1]) / 2
        pole = rad.ObjFullMag([pole_dimensions[0] / 4, y, -pole_dimensions[2] / 2 - gap / 2],
                              [pole_dimensions[0] / 2, pole_dimensions[1], pole_dimensions[2]],
                              zer, pole_segmentation, grp, pole_properties, pole_color)
        y += pole_dimensions[1] / 2
    # -- end magnet block
    init_magnetization = [0, magnetization_dir, 0]
    y += magnet_dimensions[1] / 4
    magnet = rad.ObjFullMag([magnet_dimensions[0] / 4, y, -magnet_dimensions[2] / 2 - gap / 2 - offset],
                            [magnet_dimensions[0] / 2, magnet_dimensions[1] / 2, magnet_dimensions[2]],
                            init_magnetization, magnet_segmentation, grp, magnet_properties, magnet_color)
    # use mirror symmetry to define the full undulator
    rad.TrfZerPerp(grp, zer, [1, 0, 0])  # reflect in the (y,z) plane
    rad.TrfZerPara(grp, zer, [0, 0, 1])  # reflect in the (x,y) plane
    rad.TrfZerPerp(grp, zer, [0, 1, 0])  # reflect in the (z,x) plane
    
    p0 = [0,-period*period_number/2,0]
    r1 = gap
    np1 = int(gap)+1
    r2 = gap
    np2 = int(gap)+1
    k_per_val = undulatorK_simple(grp, period)-2.112390751320377  #period*(1+.5*undulatorK_simple(grp, period)**2) - 46*(1+.5*2.112390751320377**2)
    km_val = km_max(grp,p0,period,period_number,r1,np1,r2,np2)
    result = np.abs(k_per_val) + 1000 * km_val#np.sqrt((k_per_val/100)**2 + km_val**2)
#     result = np.sqrt((1 / K_val)**2 + (period / 100.)**2)
    print("input parameters: ",pole_dimensions, ",k_per_val is: ", k_per_val, ",maximum kick map value is: ", km_val, "objective: ", result)#
    return result


def materials(H, M, material_type_string, magnet_remanence):
    """
    define magnetic materials for the undulator poles and magnets
    arguments:
      H    = list of magnetic field values / (Amp/m)
      M    = corresponding magnetization values / T
      material_type_string = material type string
      magnet_remanence   = remanent magnetization / T
    return: Radia representations of ...
      pole-tip material, magnet material
    """
    # -- magnetic property of poles
    ma = [[mu_0 * H[i], M[i]] for i in range(len(H))]
    mp = rad.MatSatIsoTab(ma)
    # -- permanent magnet material
    mm = rad.MatStd(material_type_string, magnet_remanence)
    return mp, mm


def undulatorK_simple(obj, per, pf_loc=None, prec=1e-5, maxIter=10000, lprint=False):
    """
    compute undulator K value
    arguments:
      obj = undulator object
      per = undulator period / m
      pf_loc = peak field location [x, y, z]. Defaults to [0, 0, 0] if not given.
      prec = precision goal for this computation
      maxIter = maximum allowed iterations
      lprint: whether or not to print results
    return:
      K = (e B_0 \lambda_u) / (2\pi m_e c)
    """
    if pf_loc is None:
        pf_loc = [0, 0, 0]
    res = rad.Solve(obj, prec, maxIter)
    peak_field = abs(rad.Fld(obj, 'bz', pf_loc))  # peak field / T
    k = e * peak_field * per * 1e-3 / (2 * np.pi * m_e * c)
    if lprint:
        print("peak field:", peak_field, "(calculated at given location",
              pf_loc, ")\nperiod is", per, "(given input)\nk is", k)
    return k

def km_max(obj,p0,per,nper,r1,np1,r2,np2,vl=[0,1,0],vt=[1,0,0]):
    """
    obj = undulator object
    p0 = the starting point of longitudinal integration
    r1 = range of the transverse grid along vt (horizontal)
    np1 = number of points in transverse direction vt (horizontal)
    r2 = range of the transverse grid along (vt cross vl, vertical)
    np2 = number of points in transverse direction (vt cross vl, vertical)
    vl = longitudinal integration direction. Defaults to [0,1,0] if not given.
    vt = one of the transverse direction (horizontal). Defaults to [1,0,0] if not given.
    """

    # default paras:
    dpar = [1,8,0,0]    #[maximum number of magnetic field harmonics to treat:1,number of longitudinal points:8,steps of transverse differentiation:0,0]
    unit = 'T2m2'     #the units for the resulting 2nd order kick values T2m2 or rad or microrad
    en = 1     #eletron energy in GeV (required only if units are rad or microrad)
    oFormat = 'fix'     #the format of the output data string: fix or tab

    km = rad.FldFocKickPer(obj,p0,vl,per,nper,vt,r1,np1,r2,np2)
    km_h = np.round(np.array(km[0]),10)
    km_v = np.round(np.array(km[1]),10)
    km_max = max(np.amax(km_h),np.amax(km_v))
    return km_max