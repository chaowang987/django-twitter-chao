# encoding: utf-8
# module twisted.test.raiser
# from /usr/lib/python3/dist-packages/twisted/test/raiser.cpython-36m-x86_64-linux-gnu.so
# by generator 1.147
"""
A trivial extension that just raises an exception.
See L{twisted.test.test_failure.test_failureConstructionWithMungedStackSucceeds}.
"""

# imports
import builtins as __builtins__ # <module 'builtins' (built-in)>

# functions

def raiseException(*args, **kwargs): # real signature unknown
    """ Raise L{RaiserException}. """
    pass

# classes

class RaiserException(Exception):
    """ A speficic exception only used to be identified in tests. """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



# variables with complex values

__loader__ = None # (!) real value is '<_frozen_importlib_external.ExtensionFileLoader object at 0x7f09f34faac8>'

__spec__ = None # (!) real value is "ModuleSpec(name='twisted.test.raiser', loader=<_frozen_importlib_external.ExtensionFileLoader object at 0x7f09f34faac8>, origin='/usr/lib/python3/dist-packages/twisted/test/raiser.cpython-36m-x86_64-linux-gnu.so')"

__test__ = {}

