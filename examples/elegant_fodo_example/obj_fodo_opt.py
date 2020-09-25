from rsbeams.rsdata.SDDS import readSDDS

def obj_f(_):
    sdds = readSDDS('../../tests/support/twiss_output.filename.sdds')
    sdds.read()

    nux = sdds.parameters['nux'][0][0]
    nuy = sdds.parameters['nuy'][0][0]

    obj = (nux - 0.25)**2 + (nuy - 0.25)**2

    return obj

