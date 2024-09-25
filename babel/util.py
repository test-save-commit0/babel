"""
    babel.util
    ~~~~~~~~~~

    Various utility classes and functions.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import codecs
import collections
import datetime
import os
import re
import textwrap
from collections.abc import Generator, Iterable
from typing import IO, Any, TypeVar
from babel import dates, localtime
missing = object()
_T = TypeVar('_T')


def distinct(iterable: Iterable[_T]) ->Generator[_T, None, None]:
    """Yield all items in an iterable collection that are distinct.

    Unlike when using sets for a similar effect, the original ordering of the
    items in the collection is preserved by this function.

    >>> print(list(distinct([1, 2, 1, 3, 4, 4])))
    [1, 2, 3, 4]
    >>> print(list(distinct('foobar')))
    ['f', 'o', 'b', 'a', 'r']

    :param iterable: the iterable collection providing the data
    """
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item


PYTHON_MAGIC_COMMENT_re = re.compile(
    b'[ \\t\\f]* \\# .* coding[=:][ \\t]*([-\\w.]+)', re.VERBOSE)


def parse_encoding(fp: IO[bytes]) ->(str | None):
    """Deduce the encoding of a source file from magic comment.

    It does this in the same way as the `Python interpreter`__

    .. __: https://docs.python.org/3.4/reference/lexical_analysis.html#encoding-declarations

    The ``fp`` argument should be a seekable file object.

    (From Jeff Dairiki)
    """
    pos = fp.tell()
    fp.seek(0)
    try:
        line1 = fp.readline()
        if line1 and line1.startswith(codecs.BOM_UTF8):
            return 'utf-8'
        line2 = fp.readline()
        for line in (line1, line2):
            match = PYTHON_MAGIC_COMMENT_re.search(line)
            if match:
                return match.group(1).decode('ascii')
    finally:
        fp.seek(pos)
    return None


PYTHON_FUTURE_IMPORT_re = re.compile(
    'from\\s+__future__\\s+import\\s+\\(*(.+)\\)*')


def parse_future_flags(fp: IO[bytes], encoding: str='latin-1') ->int:
    """Parse the compiler flags by :mod:`__future__` from the given Python
    code.
    """
    import __future__
    flags = 0
    pos = fp.tell()
    fp.seek(0)
    try:
        for line in fp:
            match = PYTHON_FUTURE_IMPORT_re.search(line.decode(encoding))
            if match:
                for feature in match.group(1).split(','):
                    feature = feature.strip()
                    if hasattr(__future__, feature):
                        flags |= getattr(__future__, feature).compiler_flag
    finally:
        fp.seek(pos)
    return flags


def pathmatch(pattern: str, filename: str) ->bool:
    """Extended pathname pattern matching.

    This function is similar to what is provided by the ``fnmatch`` module in
    the Python standard library, but:

     * can match complete (relative or absolute) path names, and not just file
       names, and
     * also supports a convenience pattern ("**") to match files at any
       directory level.

    Examples:

    >>> pathmatch('**.py', 'bar.py')
    True
    >>> pathmatch('**.py', 'foo/bar/baz.py')
    True
    >>> pathmatch('**.py', 'templates/index.html')
    False

    >>> pathmatch('./foo/**.py', 'foo/bar/baz.py')
    True
    >>> pathmatch('./foo/**.py', 'bar/baz.py')
    False

    >>> pathmatch('^foo/**.py', 'foo/bar/baz.py')
    True
    >>> pathmatch('^foo/**.py', 'bar/baz.py')
    False

    >>> pathmatch('**/templates/*.html', 'templates/index.html')
    True
    >>> pathmatch('**/templates/*.html', 'templates/foo/bar.html')
    False

    :param pattern: the glob pattern
    :param filename: the path name of the file to match against
    """
    import fnmatch
    parts = filename.split(os.path.sep)
    patterns = pattern.split(os.path.sep)
    
    for idx, part in enumerate(patterns):
        if part == '**':
            return fnmatch.fnmatch(os.path.sep.join(parts[idx:]), os.path.sep.join(patterns[idx + 1:]))
    
    return fnmatch.fnmatch(filename, pattern)


class TextWrapper(textwrap.TextWrapper):
    wordsep_re = re.compile(
        '(\\s+|(?<=[\\w\\!\\"\\\'\\&\\.\\,\\?])-{2,}(?=\\w))')


def wraptext(text: str, width: int=70, initial_indent: str='',
    subsequent_indent: str='') ->list[str]:
    """Simple wrapper around the ``textwrap.wrap`` function in the standard
    library. This version does not wrap lines on hyphens in words.

    :param text: the text to wrap
    :param width: the maximum line width
    :param initial_indent: string that will be prepended to the first line of
                           wrapped output
    :param subsequent_indent: string that will be prepended to all lines save
                              the first of wrapped output
    """
    wrapper = TextWrapper(width=width,
                          initial_indent=initial_indent,
                          subsequent_indent=subsequent_indent,
                          break_long_words=False,
                          break_on_hyphens=False)
    return wrapper.wrap(text)


odict = collections.OrderedDict


class FixedOffsetTimezone(datetime.tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset: float, name: (str | None)=None) ->None:
        self._offset = datetime.timedelta(minutes=offset)
        if name is None:
            name = 'Etc/GMT%+d' % offset
        self.zone = name

    def __str__(self) ->str:
        return self.zone

    def __repr__(self) ->str:
        return f'<FixedOffset "{self.zone}" {self._offset}>'


UTC = dates.UTC
LOCALTZ = dates.LOCALTZ
get_localzone = localtime.get_localzone
STDOFFSET = localtime.STDOFFSET
DSTOFFSET = localtime.DSTOFFSET
DSTDIFF = localtime.DSTDIFF
ZERO = localtime.ZERO
