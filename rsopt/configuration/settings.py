

def read_setting_dict(input):
    for name, values in input.items():
        yield name, values


_SETTING_READERS = {
    dict: read_setting_dict
}


class Settings:
    def __init__(self):
        self.settings = {}

    def parse(self, name, value):
        self.settings[name] = value