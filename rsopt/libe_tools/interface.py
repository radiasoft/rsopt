import importlib

# FUTURE: This will probably be moved to interface specific modules if more than nlopt are supported
#   and the method check and return abstracted


def get_local_optimizer_method(method, package_name):
    if package_name == 'nlopt':
        package = importlib.import_module(package_name)
        assert hasattr(package, method), f'{method} is not a valid optimization method in {package_name}'
        return method
    elif package_name == 'dfols':
        assert method == 'dfols' or not method, f'Method, {method}, is not valid for dfols. Only method: dfols is allowed'
        return method
    elif package_name == 'scipy':
        software_options = ('Nelder-Mead', 'COBYLA', 'BFGS')
        message = f"Method, {method} is not an available option from scipy in rsopt. Please use one of:"
        message += ', '.join(software_options)
        assert method in software_options, message
        return 'scipy_' + method
    else:
        raise ValueError(f'software option, {package_name}, was not recognized')

