"""
Just the constants for the API, languages, error codes and so on.
"""
DEFAULT_LANGUAGE_CODE = 'en'

GENERIC_ERROR_CODE = -1
ALL_GOOD = 0
# 0-9 PERMISSIONS
NO_PERMISSION = 2
# 10-19 okish but need some help
RETURNED_EXCEPTION = 10
UNCLEAR_SEARCH = 11
NOT_FOUND = 12
# 20-29 something bad happened :(
MISSING_PARAMETER = 20
UNKNOWN_EXCEPTION = 21

# other errors
INPUT_SHOULD_BE_COORDINATES = 30
WORK_IN_PROGRESS = 9999
UNKNOWN_MODE = 77
