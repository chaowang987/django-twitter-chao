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

from .object import object

class SourceRecordFiles(object):
    """
    SourceRecordFile()
    
    Provide an easy way to look up the src records of a source package.
    """
    def __getitem__(self, *args, **kwargs): # real signature unknown
        """ Return self[key]. """
        pass

    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    def __len__(self, *args, **kwargs): # real signature unknown
        """ Return len(self). """
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    hashes = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The hashes of the source package file."""

    path = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The remote path of the source package file."""

    size = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The size of the source package file."""

    type = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The type of the source package file."""



