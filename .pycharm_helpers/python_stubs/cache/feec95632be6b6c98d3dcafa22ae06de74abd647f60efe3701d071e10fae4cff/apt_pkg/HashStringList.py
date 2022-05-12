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

class HashStringList(object):
    """
    HashStringList()
    
    Manage a list of HashStrings.
    
    The list knows which hash is the best and provides convenience
    methods for file verification.
    
    .. versionadded:: 1.1
    """
    def append(self, p_object): # real signature unknown; restored from __doc__
        """
        append(object: HashString)
        
        Append the given HashString to this list.
        """
        pass

    def find(self, type=""): # real signature unknown; restored from __doc__
        """
        find(type: str = "") -> HashString
        
        Find a hash of the given type, or the best one, if the argument
        is empty or not specified.
        """
        return HashString

    def verify_file(self, filename): # real signature unknown; restored from __doc__
        """
        verify_file(filename: str) -> bool
        
        Verify that the file with the given name matches all hashes in
        the list.
        """
        return False

    def __getitem__(self, *args, **kwargs): # real signature unknown
        """ Return self[key]. """
        pass

    def __init__(self): # real signature unknown; restored from __doc__
        pass

    def __len__(self, *args, **kwargs): # real signature unknown
        """ Return len(self). """
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        """ Create and return a new object.  See help(type) for accurate signature. """
        pass

    file_size = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """If a file size is part of the list, return it, otherwise 0."""



