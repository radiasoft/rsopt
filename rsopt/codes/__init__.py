# Templated codes have schema files that can be used to check input and create run files. Otherwise user
#   must supply module containing inputs
TEMPLATED_CODES = ['elegant', 'opal', 'madx', 'flash']

# Supported codes have defined Job class
# FUTURE: 'Unsupported' codes could become a class of supported codes that have expanded user input required to run
SUPPORTED_CODES = ['python', 'user', 'genesis', *TEMPLATED_CODES]
