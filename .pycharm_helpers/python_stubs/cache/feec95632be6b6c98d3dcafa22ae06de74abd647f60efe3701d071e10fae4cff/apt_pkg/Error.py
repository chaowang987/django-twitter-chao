# encoding: utf-8
# module apt_pkg
# from /usr/lib/python3/dist-packages/apt_pkg.cpython-36m-x86_64-linux-gnu.so
# by generator 1.147
"""
Classes and functions wrapping the apt-pkg library.

The apt_pkg module provides several classes and functions for accessing
the functionality provided by the apt-pkg library. Typical uses might
include reading APT index files and configuration files and installing
or removing packages.
"""
# no imports

from .SystemError import SystemError

class Error(SystemError):
    """
    Exception class for most python-apt exceptions.
    
    This class replaces the use of :class:`SystemError` in previous versions
    of python-apt. It inherits from :class:`SystemError`, so make sure to
    catch this class first.
    
    .. versionadded:: 1.1
    """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



