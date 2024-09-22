"""
    babel.messages.mofile
    ~~~~~~~~~~~~~~~~~~~~~

    Writing of files in the ``gettext`` MO (machine object) format.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import array
import struct
from typing import TYPE_CHECKING
from babel.messages.catalog import Catalog, Message
if TYPE_CHECKING:
    from _typeshed import SupportsRead, SupportsWrite
LE_MAGIC: int = 2500072158
BE_MAGIC: int = 3725722773


def read_mo(fileobj: SupportsRead[bytes]) ->Catalog:
    """Read a binary MO file from the given file-like object and return a
    corresponding `Catalog` object.

    :param fileobj: the file-like object to read the MO file from

    :note: The implementation of this function is heavily based on the
           ``GNUTranslations._parse`` method of the ``gettext`` module in the
           standard library.
    """
    pass


def write_mo(fileobj: SupportsWrite[bytes], catalog: Catalog, use_fuzzy:
    bool=False) ->None:
    """Write a catalog to the specified file-like object using the GNU MO file
    format.

    >>> import sys
    >>> from babel.messages import Catalog
    >>> from gettext import GNUTranslations
    >>> from io import BytesIO

    >>> catalog = Catalog(locale='en_US')
    >>> catalog.add('foo', 'Voh')
    <Message ...>
    >>> catalog.add((u'bar', u'baz'), (u'Bahr', u'Batz'))
    <Message ...>
    >>> catalog.add('fuz', 'Futz', flags=['fuzzy'])
    <Message ...>
    >>> catalog.add('Fizz', '')
    <Message ...>
    >>> catalog.add(('Fuzz', 'Fuzzes'), ('', ''))
    <Message ...>
    >>> buf = BytesIO()

    >>> write_mo(buf, catalog)
    >>> x = buf.seek(0)
    >>> translations = GNUTranslations(fp=buf)
    >>> if sys.version_info[0] >= 3:
    ...     translations.ugettext = translations.gettext
    ...     translations.ungettext = translations.ngettext
    >>> translations.ugettext('foo')
    u'Voh'
    >>> translations.ungettext('bar', 'baz', 1)
    u'Bahr'
    >>> translations.ungettext('bar', 'baz', 2)
    u'Batz'
    >>> translations.ugettext('fuz')
    u'fuz'
    >>> translations.ugettext('Fizz')
    u'Fizz'
    >>> translations.ugettext('Fuzz')
    u'Fuzz'
    >>> translations.ugettext('Fuzzes')
    u'Fuzzes'

    :param fileobj: the file-like object to write to
    :param catalog: the `Catalog` instance
    :param use_fuzzy: whether translations marked as "fuzzy" should be included
                      in the output
    """
    pass
