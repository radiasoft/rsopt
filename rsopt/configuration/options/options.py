# TODO: I think this is only used in aposmm. Would be nice to remove.
from rsopt.configuration.options import dfols
from rsopt.configuration.options import dlib
from rsopt.configuration.options import lh
from rsopt.configuration.options import mesh
from rsopt.configuration.options import nlopt
from rsopt.configuration.options import nsga2
from rsopt.configuration.options import aposmm
from rsopt.configuration.options import pysot
from rsopt.configuration.options import scipy
from rsopt.configuration.options import mobo

option_classes = {
    'nlopt': nlopt.Nlopt,
    'aposmm': aposmm.Aposmm,
    'nsga2': nsga2.Nsga2,
    'dfols': dfols.Dfols,
    'scipy': scipy.Scipy,
    'pysot': pysot.pySOT,
    'dlib': dlib.Dlib,
    'mobo': mobo.Mobo,
    'mesh_scan': mesh.Mesh,
    'lh_scan': lh.LH
}