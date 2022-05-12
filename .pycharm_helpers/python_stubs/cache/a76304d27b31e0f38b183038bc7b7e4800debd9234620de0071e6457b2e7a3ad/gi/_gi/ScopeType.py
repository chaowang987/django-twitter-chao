# encoding: utf-8
# module gi._gi
# from /usr/lib/python3/dist-packages/gi/_gi.cpython-36m-x86_64-linux-gnu.so
# by generator 1.147
# no doc

# imports
from gobject import (GBoxed, GEnum, GFlags, GInterface, GParamSpec, GPointer, 
    GType, Warning)

import gi as __gi
import gobject as __gobject


from .type import type

class ScopeType(type):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    ASYNC = 2
    CALL = 1
    INVALID = 0
    NOTIFIED = 3


