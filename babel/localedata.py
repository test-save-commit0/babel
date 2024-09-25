"""
    babel.localedata
    ~~~~~~~~~~~~~~~~

    Low-level locale data access.

    :note: The `Locale` class, which uses this module under the hood, provides a
           more convenient interface for accessing the locale data.

    :copyright: (c) 2013-2023 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import annotations
import os
import pickle
import re
import sys
import threading
from collections import abc
from collections.abc import Iterator, Mapping, MutableMapping
from functools import lru_cache
from itertools import chain
from typing import Any
_cache: dict[str, Any] = {}
_cache_lock = threading.RLock()
_dirname = os.path.join(os.path.dirname(__file__), 'locale-data')
_windows_reserved_name_re = re.compile('^(con|prn|aux|nul|com[0-9]|lpt[0-9])$',
    re.I)


def normalize_locale(name: str) ->(str | None):
    """Normalize a locale ID by stripping spaces and apply proper casing.

    Returns the normalized locale ID string or `None` if the ID is not
    recognized.
    """
    name = name.strip().lower()
    parts = name.split('_')
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]}_{parts[1].upper()}"
    elif len(parts) == 3:
        return f"{parts[0]}_{parts[1].upper()}_{parts[2].upper()}"
    return None


def resolve_locale_filename(name: (os.PathLike[str] | str)) ->str:
    """
    Resolve a locale identifier to a `.dat` path on disk.
    """
    name = os.fspath(name)
    if _windows_reserved_name_re.match(name):
        name = f"_{name}"
    filename = os.path.join(_dirname, f"{name}.dat")
    if not os.path.exists(filename):
        raise IOError(f"No locale data file found for '{name}'")
    return filename


def exists(name: str) ->bool:
    """Check whether locale data is available for the given locale.

    Returns `True` if it exists, `False` otherwise.

    :param name: the locale identifier string
    """
    try:
        filename = resolve_locale_filename(name)
        return os.path.isfile(filename)
    except IOError:
        return False


@lru_cache(maxsize=None)
def locale_identifiers() ->list[str]:
    """Return a list of all locale identifiers for which locale data is
    available.

    This data is cached after the first invocation.
    You can clear the cache by calling `locale_identifiers.cache_clear()`.

    .. versionadded:: 0.8.1

    :return: a list of locale identifiers (strings)
    """
    return [
        os.path.splitext(filename)[0]
        for filename in os.listdir(_dirname)
        if filename.endswith('.dat') and not filename.startswith('_')
    ]


def load(name: (os.PathLike[str] | str), merge_inherited: bool=True) ->dict[
    str, Any]:
    """Load the locale data for the given locale.

    The locale data is a dictionary that contains much of the data defined by
    the Common Locale Data Repository (CLDR). This data is stored as a
    collection of pickle files inside the ``babel`` package.

    >>> d = load('en_US')
    >>> d['languages']['sv']
    u'Swedish'

    Note that the results are cached, and subsequent requests for the same
    locale return the same dictionary:

    >>> d1 = load('en_US')
    >>> d2 = load('en_US')
    >>> d1 is d2
    True

    :param name: the locale identifier string (or "root")
    :param merge_inherited: whether the inherited data should be merged into
                            the data of the requested locale
    :raise `IOError`: if no locale data file is found for the given locale
                      identifier, or one of the locales it inherits from
    """
    global _cache
    filename = resolve_locale_filename(name)
    
    with _cache_lock:
        data = _cache.get(name)
        if data is None:
            with open(filename, 'rb') as fileobj:
                data = pickle.load(fileobj)
            _cache[name] = data
        
    if merge_inherited:
        for alias in chain([data.get('alias', {}).get('target')],
                           data.get('fallback', [])):
            if alias:
                merged = load(alias)
                merge(merged, data)
                data = merged
    
    return LocaleDataDict(data)


def merge(dict1: MutableMapping[Any, Any], dict2: Mapping[Any, Any]) ->None:
    """Merge the data from `dict2` into the `dict1` dictionary, making copies
    of nested dictionaries.

    >>> d = {1: 'foo', 3: 'baz'}
    >>> merge(d, {1: 'Foo', 2: 'Bar'})
    >>> sorted(d.items())
    [(1, 'Foo'), (2, 'Bar'), (3, 'baz')]

    :param dict1: the dictionary to merge into
    :param dict2: the dictionary containing the data that should be merged
    """
    for key, value in dict2.items():
        if key in dict1:
            if isinstance(dict1[key], MutableMapping) and isinstance(value, Mapping):
                merge(dict1[key], value)
            else:
                dict1[key] = value
        else:
            if isinstance(value, Mapping):
                dict1[key] = {}
                merge(dict1[key], value)
            else:
                dict1[key] = value


class Alias:
    """Representation of an alias in the locale data.

    An alias is a value that refers to some other part of the locale data,
    as specified by the `keys`.
    """

    def __init__(self, keys: tuple[str, ...]) ->None:
        self.keys = tuple(keys)

    def __repr__(self) ->str:
        return f'<{type(self).__name__} {self.keys!r}>'

    def resolve(self, data: Mapping[str | int | None, Any]) ->Mapping[str |
        int | None, Any]:
        """Resolve the alias based on the given data.

        This is done recursively, so if one alias resolves to a second alias,
        that second alias will also be resolved.

        :param data: the locale data
        :type data: `dict`
        """
        pass


class LocaleDataDict(abc.MutableMapping):
    """Dictionary wrapper that automatically resolves aliases to the actual
    values.
    """

    def __init__(self, data: MutableMapping[str | int | None, Any], base: (
        Mapping[str | int | None, Any] | None)=None):
        self._data = data
        if base is None:
            base = data
        self.base = base

    def __len__(self) ->int:
        return len(self._data)

    def __iter__(self) ->Iterator[str | int | None]:
        return iter(self._data)

    def __getitem__(self, key: (str | int | None)) ->Any:
        orig = val = self._data[key]
        if isinstance(val, Alias):
            val = val.resolve(self.base)
        if isinstance(val, tuple):
            alias, others = val
            val = alias.resolve(self.base).copy()
            merge(val, others)
        if isinstance(val, dict):
            val = LocaleDataDict(val, base=self.base)
        if val is not orig:
            self._data[key] = val
        return val

    def __setitem__(self, key: (str | int | None), value: Any) ->None:
        self._data[key] = value

    def __delitem__(self, key: (str | int | None)) ->None:
        del self._data[key]
