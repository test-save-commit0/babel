"""
    babel.messages.pofile
    ~~~~~~~~~~~~~~~~~~~~~

    Reading and writing of files in the ``gettext`` PO (portable object)
    format.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import os
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING
from babel.core import Locale
from babel.messages.catalog import Catalog, Message
from babel.util import _cmp, wraptext
if TYPE_CHECKING:
    from typing import IO, AnyStr
    from _typeshed import SupportsWrite
    from typing_extensions import Literal


def unescape(string: str) ->str:
    """Reverse `escape` the given string.

    >>> print(unescape('"Say:\\\\n  \\\\"hello, world!\\\\"\\\\n"'))
    Say:
      "hello, world!"
    <BLANKLINE>

    :param string: the string to unescape
    """
    return string.strip('"').replace(r'\\n', '\n').replace(r'\\"', '"').replace(r'\\', '\\')


def denormalize(string: str) ->str:
    """Reverse the normalization done by the `normalize` function.

    >>> print(denormalize(r'''""
    ... "Say:\\n"
    ... "  \\"hello, world!\\"\\n"'''))
    Say:
      "hello, world!"
    <BLANKLINE>

    >>> print(denormalize(r'''""
    ... "Say:\\n"
    ... "  \\"Lorem ipsum dolor sit "
    ... "amet, consectetur adipisicing"
    ... " elit, \\"\\n"'''))
    Say:
      "Lorem ipsum dolor sit amet, consectetur adipisicing elit, "
    <BLANKLINE>

    :param string: the string to denormalize
    """
    lines = string.strip().split('\n')
    joined = ''.join(line.strip().strip('"') for line in lines)
    return unescape(joined)


class PoFileError(Exception):
    """Exception thrown by PoParser when an invalid po file is encountered."""

    def __init__(self, message: str, catalog: Catalog, line: str, lineno: int
        ) ->None:
        super().__init__(f'{message} on {lineno}')
        self.catalog = catalog
        self.line = line
        self.lineno = lineno


class _NormalizedString:

    def __init__(self, *args: str) ->None:
        self._strs: list[str] = []
        for arg in args:
            self.append(arg)

    def __bool__(self) ->bool:
        return bool(self._strs)

    def __repr__(self) ->str:
        return os.linesep.join(self._strs)

    def __cmp__(self, other: object) ->int:
        if not other:
            return 1
        return _cmp(str(self), str(other))

    def __gt__(self, other: object) ->bool:
        return self.__cmp__(other) > 0

    def __lt__(self, other: object) ->bool:
        return self.__cmp__(other) < 0

    def __ge__(self, other: object) ->bool:
        return self.__cmp__(other) >= 0

    def __le__(self, other: object) ->bool:
        return self.__cmp__(other) <= 0

    def __eq__(self, other: object) ->bool:
        return self.__cmp__(other) == 0

    def __ne__(self, other: object) ->bool:
        return self.__cmp__(other) != 0


class PoFileParser:
    """Support class to  read messages from a ``gettext`` PO (portable object) file
    and add them to a `Catalog`

    See `read_po` for simple cases.
    """
    _keywords = ['msgid', 'msgstr', 'msgctxt', 'msgid_plural']

    def __init__(self, catalog: Catalog, ignore_obsolete: bool=False,
        abort_invalid: bool=False) ->None:
        self.catalog = catalog
        self.ignore_obsolete = ignore_obsolete
        self.counter = 0
        self.offset = 0
        self.abort_invalid = abort_invalid
        self._reset_message_state()

    def _add_message(self) ->None:
        """
        Add a message to the catalog based on the current parser state and
        clear the state ready to process the next message.
        """
        if self.msgid:
            if self.msgctxt or self.msgid_plural:
                msgid = (self.msgctxt, self.msgid)
                if self.msgid_plural:
                    msgid += (self.msgid_plural,)
            else:
                msgid = self.msgid
            message = Message(msgid,
                              self.msgstr,
                              self.locations,
                              self.flags,
                              self.auto_comments,
                              self.user_comments,
                              self.previous_msgctxt,
                              self.previous_msgid,
                              self.previous_msgid_plural,
                              self.lineno)
            self.catalog.add(message, self.offset)
        self._reset_message_state()

    def parse(self, fileobj: IO[AnyStr]) ->None:
        """
        Reads from the file-like object `fileobj` and adds any po file
        units found in it to the `Catalog` supplied to the constructor.
        """
        for line in fileobj:
            line = line.decode('utf-8') if isinstance(line, bytes) else line
            self.counter += 1
            line = line.strip()
            if not line:
                if self.in_msgstr:
                    self._add_message()
                continue

            if line.startswith('#'):
                self._process_comment(line)
            elif line.startswith('"'):
                self._process_string(line)
            elif ':' in line:
                self._process_metadata(line)
            else:
                self._process_message(line)

        if self.msgid:
            self._add_message()


def read_po(fileobj: IO[AnyStr], locale: (str | Locale | None)=None, domain:
    (str | None)=None, ignore_obsolete: bool=False, charset: (str | None)=
    None, abort_invalid: bool=False) ->Catalog:
    """Read messages from a ``gettext`` PO (portable object) file from the given
    file-like object and return a `Catalog`.

    >>> from datetime import datetime
    >>> from io import StringIO
    >>> buf = StringIO('''
    ... #: main.py:1
    ... #, fuzzy, python-format
    ... msgid "foo %(name)s"
    ... msgstr "quux %(name)s"
    ...
    ... # A user comment
    ... #. An auto comment
    ... #: main.py:3
    ... msgid "bar"
    ... msgid_plural "baz"
    ... msgstr[0] "bar"
    ... msgstr[1] "baaz"
    ... ''')
    >>> catalog = read_po(buf)
    >>> catalog.revision_date = datetime(2007, 4, 1)

    >>> for message in catalog:
    ...     if message.id:
    ...         print((message.id, message.string))
    ...         print(' ', (message.locations, sorted(list(message.flags))))
    ...         print(' ', (message.user_comments, message.auto_comments))
    (u'foo %(name)s', u'quux %(name)s')
      ([(u'main.py', 1)], [u'fuzzy', u'python-format'])
      ([], [])
    ((u'bar', u'baz'), (u'bar', u'baaz'))
      ([(u'main.py', 3)], [])
      ([u'A user comment'], [u'An auto comment'])

    .. versionadded:: 1.0
       Added support for explicit charset argument.

    :param fileobj: the file-like object to read the PO file from
    :param locale: the locale identifier or `Locale` object, or `None`
                   if the catalog is not bound to a locale (which basically
                   means it's a template)
    :param domain: the message domain
    :param ignore_obsolete: whether to ignore obsolete messages in the input
    :param charset: the character set of the catalog.
    :param abort_invalid: abort read if po file is invalid
    """
    catalog = Catalog(locale=locale, domain=domain, charset=charset)
    parser = PoFileParser(catalog, ignore_obsolete=ignore_obsolete, abort_invalid=abort_invalid)
    parser.parse(fileobj)
    return catalog


WORD_SEP = re.compile(
    '(\\s+|[^\\s\\w]*\\w+[a-zA-Z]-(?=\\w+[a-zA-Z])|(?<=[\\w\\!\\"\\\'\\&\\.\\,\\?])-{2,}(?=\\w))'
    )


def escape(string: str) ->str:
    """Escape the given string so that it can be included in double-quoted
    strings in ``PO`` files.

    >>> escape('''Say:
    ...   "hello, world!"
    ... ''')
    '"Say:\\\\n  \\\\"hello, world!\\\\"\\\\n"'

    :param string: the string to escape
    """
    return '"%s"' % string.replace('\\', '\\\\').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n').replace('"', '\\"')


def normalize(string: str, prefix: str='', width: int=76) ->str:
    """Convert a string into a format that is appropriate for .po files.

    >>> print(normalize('''Say:
    ...   "hello, world!"
    ... ''', width=None))
    ""
    "Say:\\n"
    "  \\"hello, world!\\"\\n"

    >>> print(normalize('''Say:
    ...   "Lorem ipsum dolor sit amet, consectetur adipisicing elit, "
    ... ''', width=32))
    ""
    "Say:\\n"
    "  \\"Lorem ipsum dolor sit "
    "amet, consectetur adipisicing"
    " elit, \\"\\n"

    :param string: the string to normalize
    :param prefix: a string that should be prepended to every line
    :param width: the maximum line width; use `None`, 0, or a negative number
                  to completely disable line wrapping
    """
    if width and width > 0:
        lines = []
        for idx, line in enumerate(string.splitlines(True)):
            if len(prefix + line) > width:
                chunks = []
                for chunk in WORD_SEP.split(line):
                    if chunks and len(prefix + ''.join(chunks) + chunk) > width:
                        lines.append(prefix + ''.join(chunks))
                        chunks = []
                    chunks.append(chunk)
                if chunks:
                    lines.append(prefix + ''.join(chunks))
            else:
                lines.append(prefix + line)
        string = ''.join(lines)
    
    return '""' + ''.join('\n"%s"' % line for line in escape(string).splitlines())


def write_po(fileobj: SupportsWrite[bytes], catalog: Catalog, width: int=76,
    no_location: bool=False, omit_header: bool=False, sort_output: bool=
    False, sort_by_file: bool=False, ignore_obsolete: bool=False,
    include_previous: bool=False, include_lineno: bool=True) ->None:
    """Write a ``gettext`` PO (portable object) template file for a given
    message catalog to the provided file-like object.

    >>> catalog = Catalog()
    >>> catalog.add(u'foo %(name)s', locations=[('main.py', 1)],
    ...             flags=('fuzzy',))
    <Message...>
    >>> catalog.add((u'bar', u'baz'), locations=[('main.py', 3)])
    <Message...>
    >>> from io import BytesIO
    >>> buf = BytesIO()
    >>> write_po(buf, catalog, omit_header=True)
    >>> print(buf.getvalue().decode("utf8"))
    #: main.py:1
    #, fuzzy, python-format
    msgid "foo %(name)s"
    msgstr ""
    <BLANKLINE>
    #: main.py:3
    msgid "bar"
    msgid_plural "baz"
    msgstr[0] ""
    msgstr[1] ""
    <BLANKLINE>
    <BLANKLINE>

    :param fileobj: the file-like object to write to
    :param catalog: the `Catalog` instance
    :param width: the maximum line width for the generated output; use `None`,
                  0, or a negative number to completely disable line wrapping
    :param no_location: do not emit a location comment for every message
    :param omit_header: do not include the ``msgid ""`` entry at the top of the
                        output
    :param sort_output: whether to sort the messages in the output by msgid
    :param sort_by_file: whether to sort the messages in the output by their
                         locations
    :param ignore_obsolete: whether to ignore obsolete messages and not include
                            them in the output; by default they are included as
                            comments
    :param include_previous: include the old msgid as a comment when
                             updating the catalog
    :param include_lineno: include line number in the location comment
    """
    def write(text):
        if isinstance(text, str):
            text = text.encode(catalog.charset, 'strict')
        fileobj.write(text)

    def write_comment(comment, prefix=''):
        if width and width > 0:
            wrapper = textwrap.TextWrapper(width=width,
                                           break_long_words=False)
            for line in wrapper.wrap(comment):
                write(f'#{prefix} {line}\n'.encode(catalog.charset))
        else:
            write(f'#{prefix} {comment}\n'.encode(catalog.charset))

    def write_entry(message, plural=False):
        if not no_location:
            for filename, lineno in message.locations:
                if include_lineno:
                    write(f'#: {filename}:{lineno}\n'.encode(catalog.charset))
                else:
                    write(f'#: {filename}\n'.encode(catalog.charset))
        if message.flags:
            write('#, {}\n'.format(', '.join(message.flags)).encode(catalog.charset))
        if message.auto_comments:
            for comment in message.auto_comments:
                write_comment(comment, '.')
        if message.user_comments:
            for comment in message.user_comments:
                write_comment(comment)
        if include_previous:
            write('#| msgid "{}"\n'.format(message.previous_id[0] if isinstance(message.previous_id, tuple) else message.previous_id).encode(catalog.charset))
        write('msgid {}\n'.format(normalize(message.id, width=width)).encode(catalog.charset))
        if plural:
            write('msgid_plural {}\n'.format(normalize(message.id_plural, width=width)).encode(catalog.charset))
            for idx, string in enumerate(message.string):
                write('msgstr[{}] {}\n'.format(idx, normalize(string, width=width)).encode(catalog.charset))
        else:
            write('msgstr {}\n'.format(normalize(message.string or '', width=width)).encode(catalog.charset))
        write(b'\n')

    messages = list(catalog)
    if sort_output:
        messages.sort()
    elif sort_by_file:
        messages.sort(key=lambda m: m.locations)

    if not omit_header:
        write('msgid ""\n'.encode(catalog.charset))
        write('msgstr ""\n'.encode(catalog.charset))
        headers = catalog.header_comment.splitlines()
        for header in headers:
            write('{}\n'.format(header).encode(catalog.charset))
        write(b'\n')

    for message in messages:
        if (not message.id) or (ignore_obsolete and message.obsolete):
            continue
        if isinstance(message.id, (list, tuple)):
            write_entry(message, plural=True)
        else:
            write_entry(message)

    if not ignore_obsolete:
        for message in messages:
            if message.obsolete:
                write_entry(message)


def _sort_messages(messages: Iterable[Message], sort_by: Literal['message',
    'location']) ->list[Message]:
    """
    Sort the given message iterable by the given criteria.

    Always returns a list.

    :param messages: An iterable of Messages.
    :param sort_by: Sort by which criteria? Options are `message` and `location`.
    :return: list[Message]
    """
    if sort_by == 'message':
        return sorted(messages, key=lambda m: m.id)
    elif sort_by == 'location':
        return sorted(messages, key=lambda m: m.locations[0] if m.locations else ('', 0))
    else:
        raise ValueError(f"Invalid sort_by value: {sort_by}")
