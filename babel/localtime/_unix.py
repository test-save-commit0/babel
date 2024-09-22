import datetime
import os
import re
from babel.localtime._helpers import _get_tzinfo, _get_tzinfo_from_file, _get_tzinfo_or_raise


def _get_localzone(_root: str='/') ->datetime.tzinfo:
    """Tries to find the local timezone configuration.
    This method prefers finding the timezone name and passing that to
    zoneinfo or pytz, over passing in the localtime file, as in the later
    case the zoneinfo name is unknown.
    The parameter _root makes the function look for files like /etc/localtime
    beneath the _root directory. This is primarily used by the tests.
    In normal usage you call the function without parameters.
    """
    pass
