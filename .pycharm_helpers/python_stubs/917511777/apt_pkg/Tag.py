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

class Tag(object):
    """
    Tag
    
    Identify actions to be executed on a task
    
    This is used in conjunction with :meth:`TagSection.write` to rewrite
    a tag section into a new one.
    
    This class is abstract, use one of the subclasses:
    :class:`TagRewrite`, :class:`TagRemove`, :class:`TagRename`
    
    .. versionadded:: 1.1
    """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    action = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The action to perform."""

    data = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The data to write instead (for REWRITE), or the new tag name (RENAME)"""

    name = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """The name of the tag to perform the action on."""


    REMOVE = 0
    RENAME = 1
    REWRITE = 2


