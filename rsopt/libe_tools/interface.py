import importlib

# FUTURE: This will probably be moved to interface specific modules if more than nlopt are supported
#   and the method check and return abstracted


def get_local_optimizer_method(method, package):
    importlib.import_module(package)

    assert hasattr(package, method), f'{method} is not a valid optimization method in f{package}'

    return method

