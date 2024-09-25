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
    if not message.pluralizable:
        return
    
    if catalog and catalog.num_plurals:
        expected = catalog.num_plurals
    elif message.pluralizable:
        expected = len(message.id)
    else:
        return

    found = len(message.string)
    if found != expected:
        raise TranslationError(f"Expected {expected} plurals, found {found}")


def python_format(catalog: (Catalog | None), message: Message) ->None:
    """Verify the format string placeholders in the translation."""
    if PYTHON_FORMAT not in message.flags:
        return

    if isinstance(message.id, (list, tuple)):
        ids = message.id
    else:
        ids = [message.id]

    strings = message.string if isinstance(message.string, (list, tuple)) else [message.string]

    for msgid, msgstr in zip(ids, strings):
        if msgid and msgstr:
            _validate_format(msgid, msgstr)


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
    import re

    def parse_format(s):
        return [(m.group(1) or m.group(2), m.group(3))
                for m in re.finditer(r'%(?:(\([^)]+\))?([#0 +-]?\d*(?:\.\d+)?[hlL]?[diouxXeEfFgGcrs%])|(.)', s)]

    def are_compatible(a, b):
        if a == b:
            return True
        for compat in _string_format_compatibilities:
            if a in compat and b in compat:
                return True
        return False

    format_specs = parse_format(format)
    alternative_specs = parse_format(alternative)

    if len(format_specs) != len(alternative_specs):
        raise TranslationError("Different number of placeholders")

    for (f_name, f_type), (a_name, a_type) in zip(format_specs, alternative_specs):
        if not are_compatible(f_type, a_type):
            raise TranslationError(f"Incompatible format types: {f_type} and {a_type}")
        if f_name != a_name:
            raise TranslationError(f"Mismatched placeholder names: {f_name} and {a_name}")


checkers: list[Callable[[Catalog | None, Message], object]] = _find_checkers()
