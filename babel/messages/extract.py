"""
    babel.messages.extract
    ~~~~~~~~~~~~~~~~~~~~~~

    Basic infrastructure for extracting localizable messages from source files.

    This module defines an extensible system for collecting localizable message
    strings from a variety of sources. A native extractor for Python source
    files is builtin, extractors for other sources can be added using very
    simple plugins.

    The main entry points into the extraction functionality are the functions
    `extract_from_dir` and `extract_from_file`.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import ast
import io
import os
import sys
import tokenize
from collections.abc import Callable, Collection, Generator, Iterable, Mapping, MutableSequence
from os.path import relpath
from textwrap import dedent
from tokenize import COMMENT, NAME, OP, STRING, generate_tokens
from typing import TYPE_CHECKING, Any
from babel.util import parse_encoding, parse_future_flags, pathmatch
if TYPE_CHECKING:
    from typing import IO, Protocol
    from _typeshed import SupportsItems, SupportsRead, SupportsReadline
    from typing_extensions import Final, TypeAlias, TypedDict


    class _PyOptions(TypedDict, total=(False)):
        encoding: str


    class _JSOptions(TypedDict, total=(False)):
        encoding: str
        jsx: bool
        template_string: bool
        parse_template_string: bool


    class _FileObj(SupportsRead[bytes], SupportsReadline[bytes], Protocol):
        pass
    _SimpleKeyword: TypeAlias = tuple[int | tuple[int, int] | tuple[int,
        str], ...] | None
    _Keyword: TypeAlias = dict[int | None, _SimpleKeyword] | _SimpleKeyword
    _FileExtractionResult: TypeAlias = tuple[str, int, str | tuple[str, ...
        ], list[str], str | None]
    _ExtractionResult: TypeAlias = tuple[int, str | tuple[str, ...], list[
        str], str | None]
    _CallableExtractionMethod: TypeAlias = Callable[[_FileObj | IO[bytes],
        Mapping[str, _Keyword], Collection[str], Mapping[str, Any]],
        Iterable[_ExtractionResult]]
    _ExtractionMethod: TypeAlias = _CallableExtractionMethod | str
GROUP_NAME: Final[str] = 'babel.extractors'
DEFAULT_KEYWORDS: dict[str, _Keyword] = {'_': None, 'gettext': None,
    'ngettext': (1, 2), 'ugettext': None, 'ungettext': (1, 2), 'dgettext':
    (2,), 'dngettext': (2, 3), 'N_': None, 'pgettext': ((1, 'c'), 2),
    'npgettext': ((1, 'c'), 2, 3)}
DEFAULT_MAPPING: list[tuple[str, str]] = [('**.py', 'python')]
FSTRING_START = getattr(tokenize, 'FSTRING_START', None)
FSTRING_MIDDLE = getattr(tokenize, 'FSTRING_MIDDLE', None)
FSTRING_END = getattr(tokenize, 'FSTRING_END', None)


def _strip_comment_tags(comments: MutableSequence[str], tags: Iterable[str]):
    """Helper function for `extract` that strips comment tags from strings
    in a list of comment lines.  This functions operates in-place.
    """
    pass


def extract_from_dir(dirname: (str | os.PathLike[str] | None)=None,
    method_map: Iterable[tuple[str, str]]=DEFAULT_MAPPING, options_map: (
    SupportsItems[str, dict[str, Any]] | None)=None, keywords: Mapping[str,
    _Keyword]=DEFAULT_KEYWORDS, comment_tags: Collection[str]=(), callback:
    (Callable[[str, str, dict[str, Any]], object] | None)=None,
    strip_comment_tags: bool=False, directory_filter: (Callable[[str], bool
    ] | None)=None) ->Generator[_FileExtractionResult, None, None]:
    """Extract messages from any source files found in the given directory.

    This function generates tuples of the form ``(filename, lineno, message,
    comments, context)``.

    Which extraction method is used per file is determined by the `method_map`
    parameter, which maps extended glob patterns to extraction method names.
    For example, the following is the default mapping:

    >>> method_map = [
    ...     ('**.py', 'python')
    ... ]

    This basically says that files with the filename extension ".py" at any
    level inside the directory should be processed by the "python" extraction
    method. Files that don't match any of the mapping patterns are ignored. See
    the documentation of the `pathmatch` function for details on the pattern
    syntax.

    The following extended mapping would also use the "genshi" extraction
    method on any file in "templates" subdirectory:

    >>> method_map = [
    ...     ('**/templates/**.*', 'genshi'),
    ...     ('**.py', 'python')
    ... ]

    The dictionary provided by the optional `options_map` parameter augments
    these mappings. It uses extended glob patterns as keys, and the values are
    dictionaries mapping options names to option values (both strings).

    The glob patterns of the `options_map` do not necessarily need to be the
    same as those used in the method mapping. For example, while all files in
    the ``templates`` folders in an application may be Genshi applications, the
    options for those files may differ based on extension:

    >>> options_map = {
    ...     '**/templates/**.txt': {
    ...         'template_class': 'genshi.template:TextTemplate',
    ...         'encoding': 'latin-1'
    ...     },
    ...     '**/templates/**.html': {
    ...         'include_attrs': ''
    ...     }
    ... }

    :param dirname: the path to the directory to extract messages from.  If
                    not given the current working directory is used.
    :param method_map: a list of ``(pattern, method)`` tuples that maps of
                       extraction method names to extended glob patterns
    :param options_map: a dictionary of additional options (optional)
    :param keywords: a dictionary mapping keywords (i.e. names of functions
                     that should be recognized as translation functions) to
                     tuples that specify which of their arguments contain
                     localizable strings
    :param comment_tags: a list of tags of translator comments to search for
                         and include in the results
    :param callback: a function that is called for every file that message are
                     extracted from, just before the extraction itself is
                     performed; the function is passed the filename, the name
                     of the extraction method and and the options dictionary as
                     positional arguments, in that order
    :param strip_comment_tags: a flag that if set to `True` causes all comment
                               tags to be removed from the collected comments.
    :param directory_filter: a callback to determine whether a directory should
                             be recursed into. Receives the full directory path;
                             should return True if the directory is valid.
    :see: `pathmatch`
    """
    pass


def check_and_call_extract_file(filepath: (str | os.PathLike[str]),
    method_map: Iterable[tuple[str, str]], options_map: SupportsItems[str,
    dict[str, Any]], callback: (Callable[[str, str, dict[str, Any]], object
    ] | None), keywords: Mapping[str, _Keyword], comment_tags: Collection[
    str], strip_comment_tags: bool, dirpath: (str | os.PathLike[str] | None
    )=None) ->Generator[_FileExtractionResult, None, None]:
    """Checks if the given file matches an extraction method mapping, and if so, calls extract_from_file.

    Note that the extraction method mappings are based relative to dirpath.
    So, given an absolute path to a file `filepath`, we want to check using
    just the relative path from `dirpath` to `filepath`.

    Yields 5-tuples (filename, lineno, messages, comments, context).

    :param filepath: An absolute path to a file that exists.
    :param method_map: a list of ``(pattern, method)`` tuples that maps of
                       extraction method names to extended glob patterns
    :param options_map: a dictionary of additional options (optional)
    :param callback: a function that is called for every file that message are
                     extracted from, just before the extraction itself is
                     performed; the function is passed the filename, the name
                     of the extraction method and and the options dictionary as
                     positional arguments, in that order
    :param keywords: a dictionary mapping keywords (i.e. names of functions
                     that should be recognized as translation functions) to
                     tuples that specify which of their arguments contain
                     localizable strings
    :param comment_tags: a list of tags of translator comments to search for
                         and include in the results
    :param strip_comment_tags: a flag that if set to `True` causes all comment
                               tags to be removed from the collected comments.
    :param dirpath: the path to the directory to extract messages from.
    :return: iterable of 5-tuples (filename, lineno, messages, comments, context)
    :rtype: Iterable[tuple[str, int, str|tuple[str], list[str], str|None]
    """
    pass


def extract_from_file(method: _ExtractionMethod, filename: (str | os.
    PathLike[str]), keywords: Mapping[str, _Keyword]=DEFAULT_KEYWORDS,
    comment_tags: Collection[str]=(), options: (Mapping[str, Any] | None)=
    None, strip_comment_tags: bool=False) ->list[_ExtractionResult]:
    """Extract messages from a specific file.

    This function returns a list of tuples of the form ``(lineno, message, comments, context)``.

    :param filename: the path to the file to extract messages from
    :param method: a string specifying the extraction method (.e.g. "python")
    :param keywords: a dictionary mapping keywords (i.e. names of functions
                     that should be recognized as translation functions) to
                     tuples that specify which of their arguments contain
                     localizable strings
    :param comment_tags: a list of translator tags to search for and include
                         in the results
    :param strip_comment_tags: a flag that if set to `True` causes all comment
                               tags to be removed from the collected comments.
    :param options: a dictionary of additional options (optional)
    :returns: list of tuples of the form ``(lineno, message, comments, context)``
    :rtype: list[tuple[int, str|tuple[str], list[str], str|None]
    """
    pass


def extract(method: _ExtractionMethod, fileobj: _FileObj, keywords: Mapping
    [str, _Keyword]=DEFAULT_KEYWORDS, comment_tags: Collection[str]=(),
    options: (Mapping[str, Any] | None)=None, strip_comment_tags: bool=False
    ) ->Generator[_ExtractionResult, None, None]:
    """Extract messages from the given file-like object using the specified
    extraction method.

    This function returns tuples of the form ``(lineno, message, comments, context)``.

    The implementation dispatches the actual extraction to plugins, based on the
    value of the ``method`` parameter.

    >>> source = b'''# foo module
    ... def run(argv):
    ...    print(_('Hello, world!'))
    ... '''

    >>> from io import BytesIO
    >>> for message in extract('python', BytesIO(source)):
    ...     print(message)
    (3, u'Hello, world!', [], None)

    :param method: an extraction method (a callable), or
                   a string specifying the extraction method (.e.g. "python");
                   if this is a simple name, the extraction function will be
                   looked up by entry point; if it is an explicit reference
                   to a function (of the form ``package.module:funcname`` or
                   ``package.module.funcname``), the corresponding function
                   will be imported and used
    :param fileobj: the file-like object the messages should be extracted from
    :param keywords: a dictionary mapping keywords (i.e. names of functions
                     that should be recognized as translation functions) to
                     tuples that specify which of their arguments contain
                     localizable strings
    :param comment_tags: a list of translator tags to search for and include
                         in the results
    :param options: a dictionary of additional options (optional)
    :param strip_comment_tags: a flag that if set to `True` causes all comment
                               tags to be removed from the collected comments.
    :raise ValueError: if the extraction method is not registered
    :returns: iterable of tuples of the form ``(lineno, message, comments, context)``
    :rtype: Iterable[tuple[int, str|tuple[str], list[str], str|None]
    """
    pass


def extract_nothing(fileobj: _FileObj, keywords: Mapping[str, _Keyword],
    comment_tags: Collection[str], options: Mapping[str, Any]) ->list[
    _ExtractionResult]:
    """Pseudo extractor that does not actually extract anything, but simply
    returns an empty list.
    """
    pass


def extract_python(fileobj: IO[bytes], keywords: Mapping[str, _Keyword],
    comment_tags: Collection[str], options: _PyOptions) ->Generator[
    _ExtractionResult, None, None]:
    """Extract messages from Python source code.

    It returns an iterator yielding tuples in the following form ``(lineno,
    funcname, message, comments)``.

    :param fileobj: the seekable, file-like object the messages should be
                    extracted from
    :param keywords: a list of keywords (i.e. function names) that should be
                     recognized as translation functions
    :param comment_tags: a list of translator tags to search for and include
                         in the results
    :param options: a dictionary of additional options (optional)
    :rtype: ``iterator``
    """
    pass


def extract_javascript(fileobj: _FileObj, keywords: Mapping[str, _Keyword],
    comment_tags: Collection[str], options: _JSOptions, lineno: int=1
    ) ->Generator[_ExtractionResult, None, None]:
    """Extract messages from JavaScript source code.

    :param fileobj: the seekable, file-like object the messages should be
                    extracted from
    :param keywords: a list of keywords (i.e. function names) that should be
                     recognized as translation functions
    :param comment_tags: a list of translator tags to search for and include
                         in the results
    :param options: a dictionary of additional options (optional)
                    Supported options are:
                    * `jsx` -- set to false to disable JSX/E4X support.
                    * `template_string` -- if `True`, supports gettext(`key`)
                    * `parse_template_string` -- if `True` will parse the
                                                 contents of javascript
                                                 template strings.
    :param lineno: line number offset (for parsing embedded fragments)
    """
    pass


def parse_template_string(template_string: str, keywords: Mapping[str,
    _Keyword], comment_tags: Collection[str], options: _JSOptions, lineno:
    int=1) ->Generator[_ExtractionResult, None, None]:
    """Parse JavaScript template string.

    :param template_string: the template string to be parsed
    :param keywords: a list of keywords (i.e. function names) that should be
                     recognized as translation functions
    :param comment_tags: a list of translator tags to search for and include
                         in the results
    :param options: a dictionary of additional options (optional)
    :param lineno: starting line number (optional)
    """
    pass
