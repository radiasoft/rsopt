import radia as rad
import numpy as np
import scipy.constants as sc
from math import *
from copy import *
from array import array

def optimize_objective_k(lpx, lpy, lpz, pole_properties, pole_segmentation, pole_color,
                     lmx, lmz, magnet_properties, magnet_segmentation, magnet_color,
                     gap, offset, period, period_number):
    """
    create objective function based on k value
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
    return: objective function
    """
    grp, pole, magnet = hybrid_undulator(lpx, lpy, lpz, pole_properties, pole_segmentation, pole_color,
                     lmx, lmz, magnet_properties, magnet_segmentation, magnet_color,
                     gap, offset, period, period_number)
    K_val = undulatorK_simple(grp, period)
    result = np.sqrt((1 / K_val)**2 + (period / 100.)**2)
    print('period:', period,', lpy:', lpy,', lmz:',lmz,', lpz:', lpz,', offset:',offset, ', k:',K_val,', objective:',result)
    return result


def optimize_objective_km(lpx, lpy, lpz, pole_properties, pole_segmentation, pole_color,
                     lmx, lmz, magnet_properties, magnet_segmentation, magnet_color,
                     gap, offset, period, period_number):
    """
    create objective function based on the maximum value of the kick maps
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
    return: objective function
    """
    grp, pole, magnet = hybrid_undulator(lpx, lpy, lpz, pole_properties, pole_segmentation, pole_color,
                     lmx, lmz, magnet_properties, magnet_segmentation, magnet_color,
                     gap, offset, period, period_number)
    p0 = [0,-period*period_number/2,0]
    r1 = 0.75*gap
    np1 = 21
    r2 = 0.75*gap
    np2 = 21
    k_per_val = undulatorK_simple(grp, period)-2.112390751320377
    km_val = km_max(grp,p0,period,period_number,r1,np1,r2,np2)
    result = np.abs(k_per_val) + 10000 * km_val
    print("lp: ",[lpx, lpy, lpz], ",k-k0 is: ", k_per_val, ",maximum kick map value is: ", km_val, "objective: ", result)
    return result

def optimize_objective_km_appleII(period, period_number, gap, gapx, phase, phaseType, lx, lz, cx, cz, air, br, mu, nDiv, bs1_fac, bs2_fac, bs3_fac, s1_fac, s2_fac, s3_fac, bs2dz, indsMagDispQP, vertMagDispQP, _use_sym=False):
    """
    create objective function based on the maximum value of the kick maps of an appleII type undulator
    arguments:
      period = length of one undulator period / mm
      period_number = number of full periods of the undulator magnetic field
      gap = vertical magnetic gap / mm
      gapx = horizontal gap between magnet arrays /mm
      phase = longitudinal shift between magnet arrays
      phaseType = 1 means parallel, -1 anti-parallel displacement of magnet arrays
      lx = horizontal magnet size
      lz = vertical magnet size
      cx = horizontal notch size
      cz = vertical notch size
      air = air space between magnets in longitudinal direction
      br = remanent magnetization
      mu = suscettivita
      nDiv = subdivision params
      bs1_fac = terminations: magnet D2 bs1/period
      bs2_fac = terminations: magnet C bs2/period
      bs3_fac = terminations: magnet D1 bs3/period
      s1_fac = terminations: outmost gap G2 s1/period
      s2_fac = terminations: inmost gap G1 s2/period
      s3_fac = terminations: s3/period
      bs2dz = vertical displacement of vertically-magnetised termination block
      indsMagDispQP = indexes of magnets counting from the central magnet of the structure, which has index 0.
      vertMagDispQP = 0
    return: objective function
    """
    #Terminations
    bs3 = bs3_fac*period #8.43/57.2*per (*7.89*per/105.2;*) (*7.25*per/49.2;*)  (*11.2*per/80.;*) #Magnet D1
    bs2 = bs2_fac*period #7.09/57.2*per #(*13.10*per/105.2;*) (*6.11*per/49.2;*) (*9.985*per/80.;*) #Magnet C
    bs1 = bs1_fac*period #6.58/57.2*per #(*13.56*per/105.2;*)(*3.82*per/49.2;*) (*7.9*per/80.;*) #Magnet D2
    s1 = s1_fac*period #1.41*per/57.2 #(*4.63*per/105.2;*)  (*1.*per/49.2;*)   (*2.4261*per/80.; *) #Outmost Gap G2
    s2 = s2_fac*period #3.84*per/57.2 #(*2.47*per/105.2;*) (*4.5*per/49.2;*) (*5.7595*per/80.;*) #Inmost Gap G1
    s3 = s3_fac*period #0. #(*1.*per/49.2;*) (*1.;*)(*0.;*)

    #Start Computations
    grp = APPLE_II(_per=period, _nper=period_number, _gap=gap, _gapx=gapx, _phase=phase, _phase_type=phaseType, _lx=lx, _lz=lz, _cx=cx, _cz=cz, _air=air,
                   _br=br, _mu=mu, _ndiv=nDiv, _bs1=bs1, _s1=s1, _bs2=bs2, _s2=s2, _bs3=bs3, _s3=s3, _bs2dz=bs2dz,
                   _qp_ind_mag=indsMagDispQP, _qp_dz=vertMagDispQP, _use_sym=True)[0]
    
    p0 = [0,-period*period_number/2,0]
    r1 = 0.75*gap
    np1 = 21
    r2 = 0.75*gap
    np2 = 21
    k_per_val = undulatorK_simple(grp, period)-4.579876009296463
    km_val = km_max(grp,p0,period,period_number,r1,np1,r2,np2)
    result = np.abs(k_per_val) + 100 * km_val
    print("(lx, lz, cx, cz): ",[lx, lz, cx, cz], ",k-k0 is: ", k_per_val, ",maximum kick map value is: ", km_val, "objective: ", result)#",k-k0 is: ", k_per_val, 
    return result

def optimize_objective_1stint_appleII(period, period_number, gap, gapx, phase, phaseType, lx, lz, cx, cz, air, br, mu, nDiv, bs1_fac, bs2_fac, bs3_fac, s1_fac, s2_fac, s3_fac, bs2dz, indsMagDispQP, vertMagDispQP, _use_sym=False):
    """
    create objective function based on the 1st field integral at a certain point outside of an appleII type undulator
    arguments:
      period = length of one undulator period / mm
      period_number = number of full periods of the undulator magnetic field
      gap = vertical magnetic gap / mm
      gapx = horizontal gap between magnet arrays /mm
      phase = longitudinal shift between magnet arrays
      phaseType = 1 means parallel, -1 anti-parallel displacement of magnet arrays
      lx = horizontal magnet size
      lz = vertical magnet size
      cx = horizontal notch size
      cz = vertical notch size
      air = air space between magnets in longitudinal direction
      br = remanent magnetization
      mu = suscettivita
      nDiv = subdivision params
      bs1_fac = terminations: magnet D2 bs1/period
      bs2_fac = terminations: magnet C bs2/period
      bs3_fac = terminations: magnet D1 bs3/period
      s1_fac = terminations: outmost gap G2 s1/period
      s2_fac = terminations: inmost gap G1 s2/period
      s3_fac = terminations: s3/period
      bs2dz = vertical displacement of vertically-magnetised termination block
      indsMagDispQP = indexes of magnets counting from the central magnet of the structure, which has index 0.
      vertMagDispQP = 0
    return: objective function
    """
    
    #Terminations
    bs3 = bs3_fac*period #8.43/57.2*per (*7.89*per/105.2;*) (*7.25*per/49.2;*)  (*11.2*per/80.;*) #Magnet D1
    bs2 = bs2_fac*period #7.09/57.2*per #(*13.10*per/105.2;*) (*6.11*per/49.2;*) (*9.985*per/80.;*) #Magnet C
    bs1 = bs1_fac*period #6.58/57.2*per #(*13.56*per/105.2;*)(*3.82*per/49.2;*) (*7.9*per/80.;*) #Magnet D2
    s1 = s1_fac*period #1.41*per/57.2 #(*4.63*per/105.2;*)  (*1.*per/49.2;*)   (*2.4261*per/80.; *) #Outmost Gap G2
    s2 = s2_fac*period #3.84*per/57.2 #(*2.47*per/105.2;*) (*4.5*per/49.2;*) (*5.7595*per/80.;*) #Inmost Gap G1
    s3 = s3_fac*period #0. #(*1.*per/49.2;*) (*1.;*)(*0.;*)

    #Start Computations
    grp = APPLE_II(_per=period, _nper=period_number, _gap=gap, _gapx=gapx, _phase=phase, _phase_type=phaseType, _lx=lx, _lz=lz, _cx=cx, _cz=cz, _air=air,
                   _br=br, _mu=mu, _ndiv=nDiv, _bs1=bs1, _s1=s1, _bs2=bs2, _s2=s2, _bs3=bs3, _s3=s3, _bs2dz=bs2dz,
                   _qp_ind_mag=indsMagDispQP, _qp_dz=vertMagDispQP, _use_sym=True)[0]
    
    k_per_val = undulatorK_simple(grp, period)-4.579876009296463
    Bz_int1st = undulator_1st_int(grp, period, period_number)
    result = 1000*np.sqrt(Bz_int1st**2)#np.abs(k_per_val) + 100 * Bz_int1st
    print("(bs1_fac, bs2_fac, bs3_fac, s1_fac, s2_fac, s3_fac, bs2dz): ",[bs1_fac, bs2_fac, bs3_fac, s1_fac, s2_fac, s3_fac, bs2dz], ",k-k0 is: ", k_per_val, ",first field integral is: ", Bz_int1st, "objective: ", result)#",k-k0 is: ", k_per_val, 
    return result

# From RadiaToTrack.m
def undparts(po, wv, wh, nnp, per, br, si, axe=0.):
    """
    create Pure Permanent Magnet
    """
    g = rad.ObjCnt([])
    p = po - [0, nnp*per/2, 0]
    for i in range(0,4*nnp + 1):
        if i == 0 or i == 4*nnp: s = 0.5
        else: s = 1.
        if i%2 == 0: w = wv
        else: w = wh
        t = -(i - 1)*np.pi/2*si
        m = np.array([np.sin(axe)*np.sin(t), np.cos(t), np.cos(axe)*np.sin(t)])*br*s
        ma = rad.ObjRecMag(p, w, m)
        rad.ObjAddToCnt(g, [ma])
        p = p + [0, per/4, 0]
    rad.ObjDrwAtr(g, [0, 0, 1])
    return g

def apple2G(pos, per, gap, gapx, plr, pll, pur, pul, lx, lz, airgap, br, nper):
    """
    create "Apple II" type undulator
    """
    wv = [lx/2, per/4 - airgap, lz]
    wh = wv
    px = lx/4 + gapx/2
    pz = gap/2 + lz/2
    
    g1 = undparts(pos + [px, pur, pz], wv, wh, nper, per, br, si=1)
    g2 = undparts(pos + [-px, pul, pz], wv, wh, nper, per, br, si=1)
    g3 = undparts(pos + [px, plr, -pz], wv, wh, nper, per, -br, si=-1)
    g4 = undparts(pos + [-px, pll, -pz], wv, wh, nper, per, -br, si=-1)

    g = rad.ObjCnt([g1, g2, g3, g4])
    return g

def apple2(pos, per, gap, gapx, phase, lx, lz, airgap, br, nper):
    wv = [lx/2, per/4 - airgap, lz]
    wh = wv
    px = lx/4 + gapx/2
    pz = gap/2 + lz/2
    
    g1 = undparts(pos + [px, phase/2, pz], wv, wh, nper, per, br, 1)
    g2 = undparts(pos + [-px, -phase/2, pz], wv, wh, nper, per, br, 1)
    g3 = undparts(pos + [px, -phase/2, -pz], wv, wh, nper, per, -br, -1)
    g4 = undparts(pos + [-px, phase/2, -pz], wv, wh, nper, per, -br, -1)
    g = rad.ObjCnt([g1, g2, g3, g4])
    return g

def sp8(pos, per, gap, gapx, phase, lxc, lzc, colc, lxs, lzs, cols, airgap, br, nper):
    """
    create "Spring8" undulator
    """
    wc = [lxc, per/4 - airgap, lzc]
    px = 0
    pz = gap/2 + lzc/2
    g1 = undparts(pos + [px, -phase/2, pz], wc, wc, nper, per, br, 1)
    rad.ObjDrwAtr(g1, colc)
    g2 = undparts(pos + [px, -phase/2, -pz], wc, wc, nper, per, -br, -1)
    rad.ObjDrwAtr(g2, colc)
    wc = [lxs, per/4 - airgap, lzs]
    px = lxc/2 + gapx + lxs/2
    pz = gap/2 + lzs/2
    
    g3 = undparts(pos + [px, phase/2, pz], wc, wc, nper, per, br, 1)
    rad.ObjDrwAtr(g3, cols)
    g4 = undparts(pos + [px, phase/2, -pz], wc, wc, nper, per, br, -1)
    rad.ObjDrwAtr(g4, cols)
    g5 = undparts(pos + [-px, phase/2, pz], wc, wc, nper, per, -br, 1)
    rad.ObjDrwAtr(g5, cols)
    g6 = undparts(pos + [-px, phase/2, -pz], wc, wc, nper, per, -br, -1)
    rad.ObjDrwAtr(g6, cols)
    
    g = rad.ObjCnt([g1, g2, g3, g4, g5, g6])
    return g


# From RADIA_APPLE_II_Demo.py
def MagnetBlock(_pc, _wc, _cx, _cz, _type, _ndiv, _m):

    u = rad.ObjCnt([])
    
    wwc = _wc
    if(_type!=0):
        wwc = copy(_wc)
        wwc[0] -= 2*_cx
        
    b1 = rad.ObjRecMag(_pc, wwc, _m)
    rad.ObjAddToCnt(u, [b1])
    #ndiv2 = [1,_ndiv[1],_ndiv[2]]

    if((_cx>0.01) and (_cz>0.01)):
        if(_type==1):
            ppc = [_pc[0]-_wc[0]/2+_cx/2,_pc[1],_pc[2]-_cz/2]
            wwc = [_cx,_wc[1],_wc[2]-_cz]
            b2 = rad.ObjRecMag(ppc, wwc, _m)

            ppc = [_pc[0]+_wc[0]/2-_cx/2,_pc[1],_pc[2]+_cz/2]
            wwc = [_cx,_wc[1],_wc[2]-_cz]
            b3 = rad.ObjRecMag(ppc, wwc, _m)
            rad.ObjAddToCnt(u, [b2,b3])

        elif(_type==2):
            ppc = [_pc[0]-_wc[0]/2+_cx/2,_pc[1],_pc[2]+_cz/2]
            wwc = [_cx,_wc[1],_wc[2]-_cz]
            b2 = rad.ObjRecMag(ppc, wwc, _m)

            ppc = [_pc[0]+_wc[0]/2-_cx/2,_pc[1],_pc[2]-_cz/2]
            wwc = [_cx,_wc[1],_wc[2]-_cz]
            b3 = rad.ObjRecMag(ppc, wwc, _m)
            rad.ObjAddToCnt(u, [b2,b3])

        elif(_type==3):
            ppc = [_pc[0]-_wc[0]/2+_cx/2,_pc[1],_pc[2]]
            wwc = [_cx,_wc[1],_wc[2]-2*_cz]
            b2 = rad.ObjRecMag(ppc, wwc, _m)

            ppc = [_pc[0]+_wc[0]/2-_cx/2,_pc[1],_pc[2]]
            wwc = [_cx,_wc[1],_wc[2]-2*_cz]
            b3 = rad.ObjRecMag(ppc, wwc, _m)
            rad.ObjAddToCnt(u, [b2,b3])

    rad.ObjDivMag(u, _ndiv, 'Frame->LabTot')
    return u

#*************Magnet Array
def MagnetArray(_per, _nper, _po, _w, _si, _type, _cx, _cz, _br, _mu, _ndiv, _bs1, _s1, _bs2, _s2, _bs3, _s3, _bs2dz=0, _qp_ind_mag=None, _qp_dz=0):

    u = rad.ObjCnt([])

    Le = _bs1+_s1+_bs2+_s2+_bs3+_s3
    Lc = (_nper+0.25)*_per
    p = [_po[0],_po[1]-(Lc/2+Le),_po[2]] #po-{0,(Lc/2+Le),0}

    nMagTot = 4*_nper+7
    iMagCen = int(nMagTot/2.) #0-based index of the central magnet
    #print('iMagCen =', iMagCen) #DEBUG

    QP_IsDef = False; QP_DispIsConst = True
    nQP_Disp = 0
    if(_qp_ind_mag is not None):
        if(isinstance(_qp_ind_mag, list) or isinstance(_qp_ind_mag, array)):
            nQP_Disp = len(_qp_ind_mag)
            if(nQP_Disp > 0): QP_IsDef = True
        if(isinstance(_qp_dz, list) or isinstance(_qp_dz, array)): QP_DispIsConst = False
        elif(_qp_dz==0): QP_IsDef = False

    for i in range(nMagTot):
        wc = copy(_w)
        
        if(i==0):
            p[1] += _bs1/2
            wc[1] = _bs1
        elif(i==1):
            p[1] += _bs1/2+_s1+_bs2/2
            wc[1] = _bs2
        elif(i==2):
            p[1] += _bs2/2+_s2+_bs3/2
            wc[1] = _bs3
        elif(i==3):
            p[1] += _bs3/2+_s3+_per/8
        elif((i>3) and (i<4*_nper+4)):
            p[1] += _per/4
        elif(i==4*_nper+4):
            p[1] += _per/8+_s3+_bs3/2
            wc[1] = _bs3
        elif(i==4*_nper+5):
            p[1] += _bs3/2+_s2+_bs2/2
            wc[1] = _bs2
        elif(i==4*_nper+6):
            p[1] += _bs2/2+_s1+_bs1/2
            wc[1] = _bs1

        pc = copy(p)

        if((i==1) or (i==4*_nper+5)):
            if(_si==1): pc[2] += _bs2dz
            else: pc[2] -= _bs2dz

        if(QP_IsDef):
            for iQP in range(nQP_Disp):
                if(i == _qp_ind_mag[iQP] + iMagCen):
                    qpdz = _qp_dz
                    if(not QP_DispIsConst): qpdz = _qp_dz[iQP]
                    pc[2] += qpdz
                    #print('Abs. Ind. of Mag. to be Displaced:', i) #DEBUG
                    break

        t = -i*pi/2*_si
        mcol = [0.0,cos(t),sin(t)]
        m = [mcol[0],mcol[1]*_br,mcol[2]*_br]

        ma = MagnetBlock(pc, wc, _cx, _cz, _type, _ndiv, m)

        mcol = [0.27, 0.9*abs(mcol[1]), 0.9*abs(mcol[2])]
        rad.ObjDrwAtr(ma, mcol, 0.0001)

        rad.ObjAddToCnt(u, [ma])

    mat = rad.MatLin(_mu, abs(_br))
    rad.MatApl(u, mat)

    return u 

#*************Undulator
def APPLE_II(_per, _nper, _gap, _gapx, _phase, _phase_type, _lx, _lz, _cx, _cz, _air, _br, _mu, _ndiv, _bs1, _s1, _bs2, _s2, _bs3, _s3, _bs2dz, _qp_ind_mag, _qp_dz, _use_sym=False):

    w = [_lx,_per/4-_air,_lz]
    px = _lx/2+_gapx/2;
    pz = _gap/2+_lz/2;

    p1 = 0; p2 = _phase; p3 = 0; p4 = _phase
    if(_phase_type < 0): p2 = -_phase

    #print('w =', w)
    g1 = MagnetArray(_per, _nper, _po=[px,p1,pz], _w=w, _si=1, _type=1, _cx=_cx, _cz=_cz, _br=_br, _mu=_mu, _ndiv=_ndiv,
                     _bs1=_bs1, _s1=_s1, _bs2=_bs2, _s2=_s2, _bs3=_bs3, _s3=_s3, _bs2dz=_bs2dz, _qp_ind_mag=_qp_ind_mag, _qp_dz=_qp_dz)

    g2 = MagnetArray(_per, _nper, _po=[-px,p2,pz], _w=w, _si=1, _type=2, _cx=_cx, _cz=_cz, _br=_br, _mu=_mu, _ndiv=_ndiv,
                     _bs1=_bs1, _s1=_s1, _bs2=_bs2, _s2=_s2, _bs3=_bs3, _s3=_s3, _bs2dz=_bs2dz, _qp_ind_mag=_qp_ind_mag, _qp_dz=_qp_dz)

    if(_use_sym):
        u = rad.ObjCnt([g1,g2])
        trf = rad.TrfCmbL(rad.TrfRot([0,0,0],[0,1,0],pi), rad.TrfInv())
        rad.TrfMlt(u, trf, 2)
        return u, g1, g2, 0, 0

    g3 = MagnetArray(_per, _nper, _po=[-px,p3,-pz], _w=w, _si=-1, _type=1, _cx=_cx, _cz=_cz, _br=-_br, _mu=_mu, _ndiv=_ndiv,
                     _bs1=_bs1, _s1=_s1, _bs2=_bs2, _s2=_s2, _bs3=_bs3, _s3=_s3, _bs2dz=_bs2dz, _qp_ind_mag=_qp_ind_mag, _qp_dz=_qp_dz)

    g4 = MagnetArray(_per, _nper, _po=[px,p4,-pz], _w=w, _si=-1, _type=2, _cx=_cx, _cz=_cz, _br=-_br, _mu=_mu, _ndiv=_ndiv,
                     _bs1=_bs1, _s1=_s1, _bs2=_bs2, _s2=_s2, _bs3=_bs3, _s3=_s3, _bs2dz=_bs2dz, _qp_ind_mag=_qp_ind_mag, _qp_dz=_qp_dz)

    u = rad.ObjCnt([g1,g2,g3,g4])
    return u, g1, g2, g3, g4


# From Radia-Example03
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


    return grp, pole, magnet


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
    ma = [[sc.mu_0 * H[i], M[i]] for i in range(len(H))]
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
    k = sc.e * peak_field * per * 1e-3 / (2 * np.pi * sc.m_e * sc.c)
    if lprint:
        print("peak field:", peak_field, "(calculated at given location",
              pf_loc, ")\nperiod is", per, "(given input)\nk is", k)
    return k

def km_max(obj,p0,per,nper,r1,np1,r2,np2,vl=[0,1,0],vt=[1,0,0]):
    """
    compute the maximum value of kickmap
    arguments:
      obj = undulator object
      p0 = the starting point of longitudinal integration
      r1 = range of the transverse grid along vt (horizontal)
      np1 = number of points in transverse direction vt (horizontal)
      r2 = range of the transverse grid along (vt cross vl, vertical)
      np2 = number of points in transverse direction (vt cross vl, vertical)
      vl = longitudinal integration direction. Defaults to [0,1,0] if not given.
      vt = one of the transverse direction (horizontal). Defaults to [1,0,0] if not given.
    return:
      the maximum value of horizontal and vertical kick
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

def undulator_1st_int(obj, per, nper, prec=1e-5, maxIter=10000):
    """
    compute undulator K value
    arguments:
      obj = undulator object
      per = undulator period / m
      nper = undulator number of periods
      prec = precision goal for this computation
      maxIter = maximum allowed iterations
    return:
      the 1st field (Bz) integral at y = per*(nper+1)
    """
#     res = rad.Solve(obj, prec, maxIter)
    Bz_int1st = rad.FldInt(obj,'fin','ibz',[0,-1e5,0],[0,per*(nper+1),0])

    return Bz_int1st