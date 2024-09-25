from __future__ import annotations
from babel.messages import frontend
try:
    from setuptools import Command
    try:
        from setuptools.errors import BaseError, OptionError, SetupError
    except ImportError:
        OptionError = SetupError = BaseError = Exception
except ImportError:
    from distutils.cmd import Command
    from distutils.errors import DistutilsSetupError as SetupError


def check_message_extractors(dist, name, value):
    """Validate the ``message_extractors`` keyword argument to ``setup()``.

    :param dist: the distutils/setuptools ``Distribution`` object
    :param name: the name of the keyword argument (should always be
                 "message_extractors")
    :param value: the value of the keyword argument
    :raise `DistutilsSetupError`: if the value is not valid
    """
    if not isinstance(value, dict):
        raise SetupError('The value of "message_extractors" must be a dictionary')

    for module, specs in value.items():
        if not isinstance(module, str):
            raise SetupError('The keys in the "message_extractors" dictionary '
                             'must be strings')
        if not isinstance(specs, list):
            raise SetupError('The values in the "message_extractors" dictionary '
                             'must be lists')
        for spec in specs:
            if not isinstance(spec, tuple) or len(spec) != 3:
                raise SetupError('Each spec in the "message_extractors" dictionary '
                                 'must be a 3-tuple')
            pattern, func, options = spec
            if not isinstance(pattern, str):
                raise SetupError('The first element in a spec must be a string')
            if not callable(func) and not isinstance(func, str):
                raise SetupError('The second element in a spec must be callable or a string')
            if not isinstance(options, dict):
                raise SetupError('The third element in a spec must be a dictionary')


class compile_catalog(frontend.CompileCatalog, Command):
    """Catalog compilation command for use in ``setup.py`` scripts.

    If correctly installed, this command is available to Setuptools-using
    setup scripts automatically. For projects using plain old ``distutils``,
    the command needs to be registered explicitly in ``setup.py``::

        from babel.messages.setuptools_frontend import compile_catalog

        setup(
            ...
            cmdclass = {'compile_catalog': compile_catalog}
        )

    .. versionadded:: 0.9
    """


class extract_messages(frontend.ExtractMessages, Command):
    """Message extraction command for use in ``setup.py`` scripts.

    If correctly installed, this command is available to Setuptools-using
    setup scripts automatically. For projects using plain old ``distutils``,
    the command needs to be registered explicitly in ``setup.py``::

        from babel.messages.setuptools_frontend import extract_messages

        setup(
            ...
            cmdclass = {'extract_messages': extract_messages}
        )
    """


class init_catalog(frontend.InitCatalog, Command):
    """New catalog initialization command for use in ``setup.py`` scripts.

    If correctly installed, this command is available to Setuptools-using
    setup scripts automatically. For projects using plain old ``distutils``,
    the command needs to be registered explicitly in ``setup.py``::

        from babel.messages.setuptools_frontend import init_catalog

        setup(
            ...
            cmdclass = {'init_catalog': init_catalog}
        )
    """


class update_catalog(frontend.UpdateCatalog, Command):
    """Catalog merging command for use in ``setup.py`` scripts.

    If correctly installed, this command is available to Setuptools-using
    setup scripts automatically. For projects using plain old ``distutils``,
    the command needs to be registered explicitly in ``setup.py``::

        from babel.messages.setuptools_frontend import update_catalog

        setup(
            ...
            cmdclass = {'update_catalog': update_catalog}
        )

    .. versionadded:: 0.9
    """


COMMANDS = {'compile_catalog': compile_catalog, 'extract_messages':
    extract_messages, 'init_catalog': init_catalog, 'update_catalog':
    update_catalog}
