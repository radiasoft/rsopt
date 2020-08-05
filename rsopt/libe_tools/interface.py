import importlib

# FUTURE: This will probably be moved to interface specific modules if more than nlopt are supported
#   and the method check and return abstracted


def get_local_optimizer_method(method, package_name):
    package = importlib.import_module(package_name)

    assert hasattr(package, method), f'{method} is not a valid optimization method in {package_name}'

    return method

