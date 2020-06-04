import importlib, os, string
from subprocess import Popen, PIPE
from . import SUCCESS, HALT, ERROR

# TODO: Change supporting file naming scheme to follow variable name from import
# TODO: Setup is declared before init of super in subclasses to give a template of required setup keys.
#   Need to institute a check of these keys.


class Template:
    def __init__(self, options):
        self.name = None
        self._options = options
        if options.get('settings'):
            self.settings = options['settings'].copy()
        else:
            self.settings = {}
        self.setup = options['setup'].copy()
        # parameters are taken in at run time (presumably from optimizer)
        self.parameters = {}
        self.input_files = []

        self.import_input()

    def import_input(self):
        input_file = self.setup['input_file']
        input_file_module = importlib.import_module(input_file)
        for key, val in input_file_module.__dict__.items():
            if not key.startswith('_'):
                self.input_files.append(val)

    def _input_file_setup(self, H, distribution_name):
        """
        Load all settings, parameters, and filenames into the runfile strings
        :return:
        """

        input_dict = {**self.settings, **H['parameters'],
                      'source_directory': self.setup['source_directory'],
                      'input_distribution': distribution_name}

        for i, _ in enumerate(self.input_files):
            self.input_files[i] = self.input_files[i].format(**input_dict)

    def _write_input_files(self, H):
        for i, input_file in enumerate(self.input_files):
            write_path = os.path.join(H['active_directory'], '{name}_{index}.in'.format(name=self.name, index=i))
            with open(write_path, 'w') as ff:
                ff.write(input_file)

    def _validate_options(self):
        required_keys = []
        for input_file in self.input_files:
            for formatter in string.Formatter().parse(input_file):
                if formatter[1] is not None:
                    assert formatter[1] != '', "{name} input files contain an unnamed Format field".format(name=self.name)
                    required_keys.append(formatter[1])

        # Check that all keys in input files are being defined in the options
        if self._options.get('settings'):
            unified_options = [key for key in self._options['settings'].keys()]
        else:
            unified_options = []
        if self._options.get('parameters'):
            unified_options += [list(key.keys())[0] for key in self._options['parameters']]
        unified_options += [key for key in self._options['setup'].keys()]
        for key in required_keys:
            if key != 'input_distribution':
                assert key in unified_options, 'Could not find {key} required by {name} input files in the provided schema'.format(key=key, name=self.name)

    def create_run_command(self, H):
        """
        Defined by subclasses
        :param H:
        :return:
        """
        return ''

    def _run_code(self, H):
        run_command = self.create_run_command(H)
        run = Popen(run_command, shell=True, stdout=PIPE, stderr=PIPE)
        return_value = run.wait()
        result, error = run.communicate()

        if error:
            # Some codes write non-error messages to stderr (OPAL)
            # Separate completion check from error logging
            with open(os.path.join(H['active_directory'], 'error_{code}.log'.format(code=self.name)), 'w') as ff:
                ff.write(error.decode())
        if return_value != 0:
            return H, ERROR

        return H, SUCCESS

    def run(self, H, distribution_name):
        """
        Function that is called by Runner.run to execute each simulation.
        Handles parameter setup from optimizer and sets distribution name
        :param H:
        :param distribution_name:
        :return:
        """
        self._input_file_setup(H, distribution_name)
        self._write_input_files(H)
        H, status = self._run_code(H)

        return H, status


class Elegant(Template):
    def __init__(self, options):
        self.setup = {
            'cores': int,
            'input_file': str,
            'source_directory': str
        }
        super(Elegant, self).__init__(options)
        self.name = 'elegant'
        self._validate_options()

    def create_run_command(self, H):
        active_directory = H['active_directory']
        prefix = 'cd {dir};'.format(dir=active_directory)
        suffix = '> log_{code}.log'.format(code=self.name)
        if self.setup['run_command'] in ['rsmpi', 'mpiexec', 'mpirun']:
            run_command = '{run_command}'.format(run_command=self.setup['run_command']) \
                          + ' -n {cores}'.format(cores=self.setup['cores'])
            if self.setup.get('server') and self.setup['run_command'] == 'rsmpi':
                run_command += ' -h {server}'.format(server=self.setup.get('server'))
            run_command += ' Pelegant'
        else:
            run_command = 'elegant'

        filename = '{code}_0.in'.format(code=self.name)
        run_command = run_command + ' {filename}'.format(filename=filename)
        run_command = prefix + ' ' + run_command + ' ' + suffix

        return run_command


class Opal(Template):
    def __init__(self, options):
        self.setup = {
            'cores': int,
            'input_file': str,
            'source_directory': str
        }
        super(Opal, self).__init__(options)
        self.name = 'opal'
        self._validate_options()

    def create_run_command(self, H):
        active_directory = H['active_directory']
        prefix = 'cd {dir};'.format(dir=active_directory)
        suffix = '> log_{code}.log'.format(code=self.name)
        if self.setup['run_command'] in ['rsmpi', 'mpiexec', 'mpirun']:
            run_command = '{run_command}'.format(run_command=self.setup['run_command']) \
                          + ' -n {cores}'.format(cores=self.setup['cores'])
            if self.setup.get('server') and self.setup['run_command'] == 'rsmpi':
                run_command += ' -h {server}'.format(server=self.setup.get('server'))
            run_command += ' opal'
        else:
            run_command = 'opal'

        filename = '{code}_0.in'.format(code=self.name)
        run_command = run_command + ' {filename}'.format(filename=filename)
        run_command = prefix + ' ' + run_command + ' ' + suffix

        return run_command


class Genesis(Template):
    def __init__(self, options):
        self.setup = {
            'cores': int,
            'input_file': str,
            'source_directory': str
        }
        super(Genesis, self).__init__(options)
        self.name = 'genesis'
        self._validate_options()

    def create_run_command(self, H):
        active_directory = H['active_directory']
        prefix = 'cd {dir};'.format(dir=active_directory)
        suffix = '> log_{code}.log'.format(code=self.name)
        if self.setup['run_command'] in ['rsmpi', 'mpiexec', 'mpirun']:
            run_command = '{run_command}'.format(run_command=self.setup['run_command']) \
                          + ' -n {cores}'.format(cores=self.setup['cores'])
            if self.setup.get('server') and self.setup['run_command'] == 'rsmpi':
                run_command += ' -h {server}'.format(server=self.setup.get('server'))
            run_command += ' genesis_mpi'
        else:
            run_command = 'genesis'

        filename = '{code}_0.in'.format(code=self.name)
        run_command = run_command + ' < {filename}'.format(filename=filename)
        run_command = prefix + ' ' + run_command + ' ' + suffix

        return run_command


code_templates = {
    'elegant': Elegant,
    'opal': Opal,
    'genesis': Genesis
}