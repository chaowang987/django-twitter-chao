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

from .Tag import Tag

class TagRewrite(Tag):
    """
    TagRewrite(name: str, data: str)
    
    Change the value of the tag to the string passed in *data*
    
    .. versionadded:: 1.1
    """
    def __init__(self, name, data): # real signature unknown; restored from __doc__
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass


