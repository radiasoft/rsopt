import yaml
import os
from uuid import uuid4
from rsbeams.rsdata.switchyard import supported_codes as switchyard_supported
from rsbeams.rsdata.switchyard import Switchyard
from .Templates import code_templates
from .Software import optimization_software
from . import SUCCESS, HALT, ERROR
# TODO: Make sure passing a null input to switchard doesn't break it so that we allow for codes generating their
#   own input distributions
# TODO: Copy the schema to the run directory
# TODO: Can't be returning H and error to the optimizer if we halt execution part way through and want to return
#  a high objective value.
# TODO: Add in directory_prefix option for for `options` in schema. Will need to make prefix or straight `directory`
#    options mutually exclusive
# TODO: Better catch for passing a non-filename into schema


class Runner:
    def __init__(self, schema, objective_function, processing=None):
        """
        Manages the running of a chain of accelerator simulation codes. The parameters for the codes and their
        ordering is set by the `schema` which is a standardized YAML file.

        The YAML file must contain a top level item 'codes' with sub items that are the name of each code to be run.
        Code names must match with `Switchyard` supported code names. Code name order is preserved and used to dictate
        order at run time. Ordering of all other keys is not significant. Each code must have 'settings' and 'setup'
        keys. Settings is not required to contain an further values, but may be used to fix values in the run files.
        'Setup' specifies how the code will be executed and the pathing to files used to run the simulation. It has
        required values which must be set (see template examples). Finally, the 'parameters' field for each code can be
        used to set a set of values which will be set by an external program (normally an optimization algorithm). The
        'parameters' field is used for convenience to record these values and can be used by other functions to set up
        the external program. The exact parameter values are passed in at execution. Parameters are not required for
        use of the Runner though.

        Code output/input conversion is handled by the the `Switchyard` module. If further modification or processing of
        output between code calls is required the user may pass functions through the `processing` parameter.
        The input format must be a dictionary with top level keys of 'pre' and/or 'post' with next level keys giving
        the code to process before or after with the value being the function to call.

        e.g.
        {'pre': {'elegant': foo, 'genesis': bar},
         'post': {'opal': foo2}
        }

        The function will receive the `H` dict.

        process foo(H):
        Will be given the H dict which contains the Switchyard for this simulation and user specified data.
        The processing script must return H and status code. The switchyard should be modified in place to adjust
        data. Other data that a user wishes to be returned at the end of the Runner job can also be passed through H.
         :returns
         H: return back a modified species object
         code: Runner code 0: continue 1: halt and return output and species 2: critical failure

        There is currently no functionality to pre-process input for the first code in the chain.
        Parameter passing to the function is not supported.

        Distributions: As the only data that must be handed off between codes distributions have special handling.
        the key {input_distribution} may be used in input files without being specified in the schema file. The runner
        will automatically generate the proper filename (of the form {from_code_name}_{to_code_name}) and insert it at
        run time.

        :param schema: Name of a YAML file or string containing YAML formatted text.
        :param objective_function: Function to be called at the end of the run to evaluate objective for optimizer
            must the return value of this function is passed out of `Runner.run`. The function is passed the `H` dict
            at evaluation. The bunch particle coordinates may be accessed by calling:
                H['switchyard'].species[!species_name]
        :param processing: Dictionary of pre/post processing functions
        """
        try:
            schema_file = open(schema, 'r')
        except FileNotFoundError:
            schema_file = schema
        self.schema = yaml.safe_load(schema_file)
        self.processing = processing
        self.objective_function = objective_function
        self.codes = []
        self.active_directory = None

        self.H = {}

        # Setup
        self._set_codes_from_schema()

    def _set_codes_from_schema(self):
        for code in self.schema['codes']:
            cd = {'code': None,
                  'pre': None,
                  'post': None
                  }
            name = list(code.keys())[0]  # There should be just one code name for each entry
            options = code[name]
            cd['code'] = code_templates[name](options)
            if self.processing:
                cd['pre'], cd['post'] = self._check_for_processing(name)
            self.codes.append(cd)

        self._check_code_support()

    def _check_for_processing(self, code_name):
        return_val = {'pre': None, 'post': None}
        for t in ['pre', 'post']:
            try:
                return_val[t] = self.processing[t][code_name]
            except KeyError:
                pass

        return return_val['pre'], return_val['post']

    def _check_code_support(self):
        for code in self.codes:
            assert code['code'].name in switchyard_supported, "{} is not supported by the Switchyard".format(code)

    def create_active_directory(self, name=None, prefix=''):
        """
        All run files and output files will go to the active directory set for the runner
        :param name: Optional name for directory. If not set the name will be created by UUID4
        :param prefix: Optional prefix to UUID named directory. Can be used to specify directory location or a name
            to join to each directory.
        :return:
        """

        if not name:
            directory_name = prefix + str(uuid4())
        else:
            directory_name = name

        try:
            os.mkdir(directory_name)
        except FileExistsError:
            print("Directory exists. You will be overwriting output files.")
            pass

        self.active_directory = directory_name

        return directory_name

    def _process_parameters(self, parameters):
        """
        Take parameters from the optimizer
        :return:
        """

        parameter_list = optimization_software[self.schema['options']['software']]['output'](self.schema, parameters)

        return parameter_list

    def prepare_parameters(self):
        """
        Helper function to prepare parameters ranges for an optimizer. Formatting depends on the optimizer software
        in use.
        
        Docstring for current optimizer:
        
        {docstring}
        
        """.format(docstring=optimization_software[self.schema['options']['software']]['input'].__doc__)

        parameters = optimization_software[self.schema['options']['software']]['input'](self.schema)

        return parameters

    def _generate_switchyard_filename(self, switchyard, code):
        name = '{input_format}_2_{output_format}'.format(input_format=switchyard.input_format, output_format=code['code'].name)
        name = os.path.join(self.active_directory, name)
        return name

    def _update_distribution(self, code):
        # Move distribution to appropriate format and run code
        filename = self._generate_switchyard_filename(self.H['switchyard'], code)
        if code['code'].setup.get('input_distribution'):
            input_distribution = code['code'].setup['input_distribution']
        else:
            input_distribution = self.H['switchyard'].write(filename, code['code'].name)
        
        # Python script is run in top level. Code commands are executed in their own directory.
        return os.path.split(input_distribution)[-1]

    def _run_code(self, code, external_distribution=True):
        # Run pre-processing
        if code['pre']:
            self.H, status = code['pre'](self.H)
            if status > SUCCESS:
                return self.H, status

        # Move distribution to appropriate format and run code and then update switchyard
        if external_distribution:
            input_distribution = self._update_distribution(code)
        else:
            input_distribution = None

        self.H, status = code['code'].run(self.H, input_distribution)
        if status > SUCCESS:
            return self.H, status

        # Update switchyard
        output_distribution = os.path.join(self.active_directory, code['code'].setup['output_distribution'])
        if code['code'].name != 'genesis':
            self.H['switchyard'] = Switchyard(output_distribution, code['code'].name)
        else:
            print("""Switchyard cannot load genesis output. H['switchyard'] will not be updated.""")

        if code['post']:
            self.H, status = code['post'](self.H)

        return self.H, status

    def run(self, input_parameters):
        # TODO: Another option here is to make run an iterable and just yield the appropriate next command
        #    this would let you pass the commands to libEnsemble or SimpleServer. Could just pass the updated H back
        #    to the run to yield next command. Or maybe not even passed to run again. Just used in conjunction with
        #    the output of run.
        """
        Execute a chain of codes and processing calls. Execution proceeds as:

        code1
        [post-process code1]

        [pre-process code2]
        [code2]
        [post-process code2]
        ... continues for all codes ...

        process objective


        :param input_parameters: Parameters for filling `parameter` fields of the schema. These is no required
            input format. This object will be processed prior to setting the schema fields based on
            the Software setting.
        :return: Output of `objective_function` if successful or (`H`, status_code) if halted early
        """
        self.H['parameters'] = self._process_parameters(input_parameters)
        directory_name = self.schema['options'].get('directory')
        self.H['active_directory'] = self.create_active_directory(name=directory_name)

        # Initialize switchyard
        if self.codes[0]['code'].setup.get('input_distribution'):
            self.H['switchyard'] = Switchyard(self.codes[0]['code'].setup['input_distribution'],
                                              self.codes[0]['code'].name)

        # Run all codes and processors
        for i, code in enumerate(self.codes):
            if i == 0:
                self.H, status = self._run_code(code, external_distribution=False)
            else:
                self.H, status = self._run_code(code, external_distribution=True)
            if status > SUCCESS:
                return self.H, status

        return self.objective_function(self.H)

