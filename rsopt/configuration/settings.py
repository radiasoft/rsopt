

def read_setting_dict(input):
    for name, values in input.items():
        yield name, values


_SETTING_READERS = {
    dict: read_setting_dict
}


class Settings:
    def __init__(self):
        self._NAMES = []
        self.settings = {}

    def parse(self, name, value):
        if name in self._NAMES:
            raise KeyError(f'Setting {name} is defined multiple times')
        self._NAMES.append(name)
        self.settings[name] = value