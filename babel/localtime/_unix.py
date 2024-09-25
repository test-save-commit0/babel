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
    # Check for the TZ environment variable
    tzenv = os.environ.get('TZ')
    if tzenv:
        return _get_tzinfo(tzenv)

    # Check for /etc/timezone file
    timezone_file = os.path.join(_root, 'etc/timezone')
    if os.path.exists(timezone_file):
        with open(timezone_file, 'r') as f:
            tzname = f.read().strip()
        if tzname:
            return _get_tzinfo_or_raise(tzname)

    # Check for /etc/localtime file
    localtime_file = os.path.join(_root, 'etc/localtime')
    if os.path.exists(localtime_file):
        return _get_tzinfo_from_file(localtime_file)

    # Check for /usr/share/zoneinfo/ symlink
    zoneinfo_dir = os.path.join(_root, 'usr/share/zoneinfo')
    if os.path.exists(zoneinfo_dir):
        for root, dirs, files in os.walk(zoneinfo_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.samefile(file_path, localtime_file):
                    tzname = os.path.relpath(file_path, zoneinfo_dir)
                    return _get_tzinfo_or_raise(tzname)

    # If all else fails, return UTC
    return _get_tzinfo('UTC')
