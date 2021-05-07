# rsopt example - derived from:
#############################################################################
# RADIA Python Test Example: Parallel (MPI based) Computation of Magnetic Field
# created by Hybrid Undulator
# v 0.01
#############################################################################

from __future__ import absolute_import, division, print_function #Py 2.*/3.* compatibility
import radia as rad
import time
import numpy as np

NP_FILENAME = 'bz.npy'


# Undulator setup
def HybridUndCenPart(_gap, _gap_ofst, _nper, _air, _lp, _ch_p, _np, _np_tip, _mp, _cp, _lm, _ch_m_xz, _ch_m_yz,
                     _ch_m_yz_r, _nm, _mm, _cm, _use_ex_sym=False):
    zer = [0, 0, 0]
    grp = rad.ObjCnt([])

    y = _lp[1] / 4
    initM = [0, -1, 0]

    pole = rad.ObjFullMag([_lp[0] / 4, y, -_lp[2] / 2 - _gap / 2 - _ch_p], [_lp[0] / 2, _lp[1] / 2, _lp[2]], zer,
                          [_np[0], int(_np[1] / 2 + 0.5), _np[2]], grp, _mp, _cp)

    if _ch_p > 0.:  # Pole Tip
        poleTip = rad.ObjThckPgn(_lp[0] / 4, _lp[0] / 2,
                                 [[y - _lp[1] / 4, -_gap / 2 - _ch_p],
                                  [y - _lp[1] / 4, -_gap / 2],
                                  [y + _lp[1] / 4 - _ch_p, -_gap / 2],
                                  [y + _lp[1] / 4, -_gap / 2 - _ch_p]], zer)
        rad.ObjDivMag(poleTip, [_np_tip[0], int(_np_tip[1] / 2 + 0.5), _np_tip[2]])
        rad.MatApl(poleTip, _mp)
        rad.ObjDrwAtr(poleTip, _cp)
        rad.ObjAddToCnt(grp, [poleTip])

    y += _lp[1] / 4 + _air + _lm[1] / 2

    for i in range(_nper):
        magnet = rad.ObjThckPgn(_lm[0] / 4, _lm[0] / 2,
                                [[y + _lm[1] / 2 - _ch_m_yz_r * _ch_m_yz, -_gap / 2 - _gap_ofst],
                                 [y + _lm[1] / 2, -_gap / 2 - _gap_ofst - _ch_m_yz],
                                 [y + _lm[1] / 2, -_gap / 2 - _gap_ofst - _lm[2] + _ch_m_yz],
                                 [y + _lm[1] / 2 - _ch_m_yz_r * _ch_m_yz, -_gap / 2 - _gap_ofst - _lm[2]],
                                 [y - _lm[1] / 2 + _ch_m_yz_r * _ch_m_yz, -_gap / 2 - _gap_ofst - _lm[2]],
                                 [y - _lm[1] / 2, -_gap / 2 - _gap_ofst - _lm[2] + _ch_m_yz],
                                 [y - _lm[1] / 2, -_gap / 2 - _gap_ofst - _ch_m_yz],
                                 [y - _lm[1] / 2 + _ch_m_yz_r * _ch_m_yz, -_gap / 2 - _gap_ofst]], initM)
        # Cuting Magnet Corners
        magnet = rad.ObjCutMag(magnet, [_lm[0] / 2 - _ch_m_xz, 0, -_gap / 2 - _gap_ofst], [1, 0, 1])[0]
        magnet = rad.ObjCutMag(magnet, [_lm[0] / 2 - _ch_m_xz, 0, -_gap / 2 - _gap_ofst - _lm[2]], [1, 0, -1])[0]

        rad.ObjDivMag(magnet, _nm)
        rad.MatApl(magnet, _mm)
        rad.ObjDrwAtr(magnet, _cm)
        rad.ObjAddToCnt(grp, [magnet])

        initM[1] *= -1
        y += _lm[1] / 2 + _lp[1] / 2 + _air

        if i < _nper-1:
            pole = rad.ObjFullMag([_lp[0]/4,y,-_lp[2]/2-_gap/2-_ch_p], [_lp[0]/2,_lp[1],_lp[2]], zer, _np, grp, _mp, _cp)

            if _ch_p > 0.:  # Pole Tip
                poleTip = rad.ObjThckPgn(_lp[0] / 4, _lp[0] / 2,
                                         [[y - _lp[1] / 2, -_gap / 2 - _ch_p],
                                          [y - _lp[1] / 2 + _ch_p, -_gap / 2],
                                          [y + _lp[1] / 2 - _ch_p, -_gap / 2],
                                          [y + _lp[1] / 2, -_gap / 2 - _ch_p]], zer)
                rad.ObjDivMag(poleTip, _np_tip)
                rad.MatApl(poleTip, _mp)
                rad.ObjDrwAtr(poleTip, _cp)
                rad.ObjAddToCnt(grp, [poleTip])

            y += _lm[1] / 2 + _lp[1] / 2 + _air

    y -= _lp[1] / 4
    pole = rad.ObjFullMag([_lp[0] / 4, y, -_lp[2] / 2 - _gap / 2 - _ch_p], [_lp[0] / 2, _lp[1] / 2, _lp[2]], zer,
                          [_np[0], int(_np[1] / 2 + 0.5), _np[2]], grp, _mp, _cp)
    if _ch_p > 0.:  # Pole Tip
        poleTip = rad.ObjThckPgn(_lp[0] / 4, _lp[0] / 2,
                                 [[y - _lp[1] / 4, -_gap / 2 - _ch_p],
                                  [y - _lp[1] / 4 + _ch_p, -_gap / 2],
                                  [y + _lp[1] / 4, -_gap / 2],
                                  [y + _lp[1] / 4, -_gap / 2 - _ch_p]], zer)
        rad.ObjDivMag(poleTip, [_np_tip[0], int(_np_tip[1] / 2 + 0.5), _np_tip[2]])
        rad.MatApl(poleTip, _mp)
        rad.ObjDrwAtr(poleTip, _cp)
        rad.ObjAddToCnt(grp, [poleTip])

    # Symmetries
    if _use_ex_sym:  # Some "non-physical" mirroring (applicable for calculation of central field only)
        y += _lp[1] / 4
        rad.TrfZerPerp(grp, [0, y, 0], [0, 1, 0])  # Mirror left-right
        rad.TrfZerPerp(grp, [0, 2 * y, 0], [0, 1, 0])

    # "Physical" symmetries (applicable also for calculation of total structure with terminations)
    rad.TrfZerPerp(grp, zer, [0, 1, 0])  # Mirror left-right
    # Mirror front-back
    rad.TrfZerPerp(grp, zer, [1, 0, 0])
    # Mirror top-bottom
    rad.TrfZerPara(grp, zer, [0, 0, 1])

    return grp


# rsopt run function
def eval_hybrid_und(_gap, _gap_ofst, _nper, _air, _pole_width, _lp, _ch_p, _np, _np_tip, _mp, _cp, _lm, _ch_m_xz,
                    _ch_m_yz, _ch_m_yz_r, _nm, _mm, _cm, _use_ex_sym=False):
    from mpi4py import MPI
    comMPI = MPI.COMM_WORLD
    size = comMPI.Get_size()
    rank = comMPI.Get_rank()
    rad.UtiMPI('in')
    
    _lp = [_pole_width, *_lp]
    
    # Set up material properties if they weren't created by a pre-process function
    if not _mp or not _mm:
        # Pole Material 
        # B [G] vs H [G] data from NEOMAX
        BvsH_G = [[0., 0], [0.5, 5000], [1, 10000], [1.5, 13000], [2, 15000], [3, 16500], [4, 17400], [6, 18500],
                  [8, 19250], [10, 19800],
                  [12, 20250], [14, 20600], [16, 20900], [18, 21120], [20, 21250], [25, 21450], [30, 21590],
                  [40, 21850], [50, 22000],
                  [70, 22170], [100, 22300], [200, 22500], [300, 22650], [500, 23000], [1000, 23900], [2000, 24900]]
        
        MvsH_T = [[BvsH_G[i][0]*1.e-4, (BvsH_G[i][1]-BvsH_G[i][0])*1.e-4] for i in range(len(BvsH_G))]
        _mp = rad.MatSatIsoTab(MvsH_T)
        
        # Magnet Material
        magBr = 1.67  # Remanent Magnetization
        _mm = rad.MatLin({0.05, 0.15}, magBr)
    
    grp = HybridUndCenPart(_gap, _gap_ofst, _nper, _air, _lp, _ch_p, _np, _np_tip, _mp, _cp, _lm, _ch_m_xz, _ch_m_yz,
                           _ch_m_yz_r, _nm, _mm, _cm, _use_ex_sym)
    
    # Construct Interaction Matrix
    t0 = time.time()
    IM = rad.RlxPre(grp)
    # Perform the Relaxation
    t0 = time.time()
    res = rad.RlxAuto(IM, 0.001, 5000)
    # Synchronizing all processes
    rad.UtiMPI('barrier')
    
    Bz0 = rad.Fld(grp, 'bz', [0,0,0])
    if rank <= 0:
        print("Bz0:", Bz0)
    if size > 1:
        if rank == 0:
            np.save(NP_FILENAME, Bz0)
    rad.UtiMPI('off')
    
    return Bz0


# preprocess function
def set_mag_properties(J):
    # Preprocessing function to setup objects that must be passed to `_mp` and `_mm`
    # Can be used with serial evaluation - otherwise eval_hybrid_und will perform this calculation
    
    # Pole Material 
    # B [G] vs H [G] data from NEOMAX
    BvsH_G = [[0., 0], [0.5, 5000], [1, 10000], [1.5, 13000], [2, 15000], [3, 16500], [4, 17400], [6, 18500],
              [8, 19250], [10, 19800],
              [12, 20250], [14, 20600], [16, 20900], [18, 21120], [20, 21250], [25, 21450], [30, 21590], [40, 21850],
              [50, 22000],
              [70, 22170], [100, 22300], [200, 22500], [300, 22650], [500, 23000], [1000, 23900], [2000, 24900]]
    MvsH_T = [[BvsH_G[i][0] * 1.e-4, (BvsH_G[i][1] - BvsH_G[i][0]) * 1.e-4] for i in range(len(BvsH_G))]
    mp = rad.MatSatIsoTab(MvsH_T)

    # Magnet Material
    magBr = 1.67  # Remanent Magnetization
    mm = rad.MatLin({0.05, 0.15}, magBr)
    print("J starts as:", J)
    J['inputs']['_mm'] = mm 
    J['inputs']['_mp'] = mp
    print("J ends as:", J)


def get_bz(J):
    # J is always passed to the objective function but is not used here
    try:
        val = float(np.load(NP_FILENAME))
    except FileNotFoundError:
        val = np.nan
    
    return val
