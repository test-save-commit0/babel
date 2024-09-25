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
    catalog = Catalog()
    buf = fileobj.read()
    buflen = len(buf)
    unpack = struct.unpack

    # Parse the magic number
    magic = unpack('<I', buf[:4])[0]
    if magic == LE_MAGIC:
        version, msgcount, masteridx, transidx = unpack('<4I', buf[4:20])
        ii = '<II'
    elif magic == BE_MAGIC:
        version, msgcount, masteridx, transidx = unpack('>4I', buf[4:20])
        ii = '>II'
    else:
        raise IOError('Invalid magic number')

    # Parse the version number
    if version != 0:
        raise IOError('Unknown MO file version')

    # Parse the catalog
    for i in range(msgcount):
        mlen, moff = unpack(ii, buf[masteridx:masteridx + 8])
        mend = moff + mlen
        tlen, toff = unpack(ii, buf[transidx:transidx + 8])
        tend = toff + tlen
        if mend > buflen or tend > buflen:
            raise IOError('File is corrupt')

        msg = buf[moff:mend].decode()
        tmsg = buf[toff:tend].decode()

        if mlen == 0:
            # Metadata
            for line in tmsg.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    catalog.metadata[key.strip()] = value.strip()
        else:
            # Regular message
            if '\x00' in msg:
                msgid, msgctxt = msg.split('\x04')
                tmsg = tmsg.split('\x00')
                catalog.add(msgid, tmsg[0], context=msgctxt)
                if len(tmsg) > 1:
                    catalog.add((msgid, msgid + '_plural'), tmsg, context=msgctxt)
            else:
                catalog.add(msg, tmsg)

        masteridx += 8
        transidx += 8

    return catalog


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
    messages = list(catalog)
    messages.sort()

    ids = strs = b''
    offsets = []

    for message in messages:
        if not message.string or (not use_fuzzy and message.fuzzy):
            continue

        if isinstance(message.id, (list, tuple)):
            msgid = '\x00'.join([m.encode('utf-8') for m in message.id])
        else:
            msgid = message.id.encode('utf-8')
        if isinstance(message.string, (list, tuple)):
            msgstr = '\x00'.join([m.encode('utf-8') for m in message.string])
        else:
            msgstr = message.string.encode('utf-8')

        offsets.append((len(ids), len(msgid), len(strs), len(msgstr)))
        ids += msgid + b'\x00'
        strs += msgstr + b'\x00'

    # The header is 28 bytes long
    keystart = 28
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets += [o1 + keystart, l1]
        voffsets += [o2 + valuestart, l2]

    offsets = koffsets + voffsets
    output = struct.pack('Iiiiiii',
        LE_MAGIC,                   # magic
        0,                          # version
        len(messages),              # number of entries
        28,                         # start of key index
        28 + len(offsets) * 4,      # start of value index
        0, 0                        # size and offset of hash table
    )
    output += array.array("i", offsets).tobytes()
    output += ids
    output += strs

    fileobj.write(output)
