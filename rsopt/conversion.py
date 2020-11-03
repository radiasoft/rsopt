
def create_switchyard(input_file, file_code):
    from rsbeams.rsdata.switchyard import Switchyard

    switchyard = Switchyard()
    switchyard.read(input_file, file_code)

    return switchyard