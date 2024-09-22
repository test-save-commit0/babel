"""
    babel.messages.jslexer
    ~~~~~~~~~~~~~~~~~~~~~~

    A simple JavaScript 1.5 lexer which is used for the JavaScript
    extractor.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import re
from collections.abc import Generator
from typing import NamedTuple
operators: list[str] = sorted(['+', '-', '*', '%', '!=', '==', '<', '>',
    '<=', '>=', '=', '+=', '-=', '*=', '%=', '<<', '>>', '>>>', '<<=',
    '>>=', '>>>=', '&', '&=', '|', '|=', '&&', '||', '^', '^=', '(', ')',
    '[', ']', '{', '}', '!', '--', '++', '~', ',', ';', '.', ':'], key=len,
    reverse=True)
escapes: dict[str, str] = {'b': '\x08', 'f': '\x0c', 'n': '\n', 'r': '\r',
    't': '\t'}
name_re = re.compile('[\\w$_][\\w\\d$_]*', re.UNICODE)
dotted_name_re = re.compile('[\\w$_][\\w\\d$_.]*[\\w\\d$_.]', re.UNICODE)
division_re = re.compile('/=?')
regex_re = re.compile('/(?:[^/\\\\]*(?:\\\\.[^/\\\\]*)*)/[a-zA-Z]*', re.DOTALL)
line_re = re.compile('(\\r\\n|\\n|\\r)')
line_join_re = re.compile('\\\\' + line_re.pattern)
uni_escape_re = re.compile('[a-fA-F0-9]{1,4}')
hex_escape_re = re.compile('[a-fA-F0-9]{1,2}')


class Token(NamedTuple):
    type: str
    value: str
    lineno: int


_rules: list[tuple[str | None, re.Pattern[str]]] = [(None, re.compile(
    '\\s+', re.UNICODE)), (None, re.compile('<!--.*')), ('linecomment', re.
    compile('//.*')), ('multilinecomment', re.compile('/\\*.*?\\*/', re.
    UNICODE | re.DOTALL)), ('dotted_name', dotted_name_re), ('name',
    name_re), ('number', re.compile(
    """(
        (?:0|[1-9]\\d*)
        (\\.\\d+)?
        ([eE][-+]?\\d+)? |
        (0x[a-fA-F0-9]+)
    )"""
    , re.VERBOSE)), ('jsx_tag', re.compile('(?:</?[^>\\s]+|/>)', re.I)), (
    'operator', re.compile('(%s)' % '|'.join(map(re.escape, operators)))),
    ('template_string', re.compile('`(?:[^`\\\\]*(?:\\\\.[^`\\\\]*)*)`', re
    .UNICODE)), ('string', re.compile(
    """(
        '(?:[^'\\\\]*(?:\\\\.[^'\\\\]*)*)'  |
        "(?:[^"\\\\]*(?:\\\\.[^"\\\\]*)*)"
    )"""
    , re.VERBOSE | re.DOTALL))]


def get_rules(jsx: bool, dotted: bool, template_string: bool) ->list[tuple[
    str | None, re.Pattern[str]]]:
    """
    Get a tokenization rule list given the passed syntax options.

    Internal to this module.
    """
    pass


def indicates_division(token: Token) ->bool:
    """A helper function that helps the tokenizer to decide if the current
    token may be followed by a division operator.
    """
    pass


def unquote_string(string: str) ->str:
    """Unquote a string with JavaScript rules.  The string has to start with
    string delimiters (``'``, ``"`` or the back-tick/grave accent (for template strings).)
    """
    pass


def tokenize(source: str, jsx: bool=True, dotted: bool=True,
    template_string: bool=True, lineno: int=1) ->Generator[Token, None, None]:
    """
    Tokenize JavaScript/JSX source.  Returns a generator of tokens.

    :param jsx: Enable (limited) JSX parsing.
    :param dotted: Read dotted names as single name token.
    :param template_string: Support ES6 template strings
    :param lineno: starting line number (optional)
    """
    pass
