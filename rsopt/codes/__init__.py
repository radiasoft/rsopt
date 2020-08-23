# Templated codes have schema files that can be used to check input and create run files. Otherwise user
#   must supply module containing inputs
_TEMPLATED_CODES = ['elegant', 'opal']

# Supported codes have defined Job class
# FUTURE: 'Unsupported' codes could become a class of supported codes that have expanded user input required to run
_SUPPORTED_CODES = ['python', 'genesis', *_TEMPLATED_CODES]
