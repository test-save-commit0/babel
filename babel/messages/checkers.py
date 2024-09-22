"""
    babel.messages.checkers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Various routines that help with validation of translations.

    :since: version 0.9

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
from collections.abc import Callable
from babel.messages.catalog import PYTHON_FORMAT, Catalog, Message, TranslationError
_string_format_compatibilities = [{'i', 'd', 'u'}, {'x', 'X'}, {'f', 'F',
    'g', 'G'}]


def num_plurals(catalog: (Catalog | None), message: Message) ->None:
    """Verify the number of plurals in the translation."""
    pass


def python_format(catalog: (Catalog | None), message: Message) ->None:
    """Verify the format string placeholders in the translation."""
    pass


def _validate_format(format: str, alternative: str) ->None:
    """Test format string `alternative` against `format`.  `format` can be the
    msgid of a message and `alternative` one of the `msgstr`\\s.  The two
    arguments are not interchangeable as `alternative` may contain less
    placeholders if `format` uses named placeholders.

    The behavior of this function is undefined if the string does not use
    string formatting.

    If the string formatting of `alternative` is compatible to `format` the
    function returns `None`, otherwise a `TranslationError` is raised.

    Examples for compatible format strings:

    >>> _validate_format('Hello %s!', 'Hallo %s!')
    >>> _validate_format('Hello %i!', 'Hallo %d!')

    Example for an incompatible format strings:

    >>> _validate_format('Hello %(name)s!', 'Hallo %s!')
    Traceback (most recent call last):
      ...
    TranslationError: the format strings are of different kinds

    This function is used by the `python_format` checker.

    :param format: The original format string
    :param alternative: The alternative format string that should be checked
                        against format
    :raises TranslationError: on formatting errors
    """
    pass


checkers: list[Callable[[Catalog | None, Message], object]] = _find_checkers()
