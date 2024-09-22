"""
    babel.localtime._fallback
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Emulated fallback local timezone when all else fails.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
import datetime
import time
STDOFFSET = datetime.timedelta(seconds=-time.timezone)
DSTOFFSET = datetime.timedelta(seconds=-time.altzone
    ) if time.daylight else STDOFFSET
DSTDIFF = DSTOFFSET - STDOFFSET
ZERO = datetime.timedelta(0)


class _FallbackLocalTimezone(datetime.tzinfo):
    pass
