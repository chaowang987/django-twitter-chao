# encoding: utf-8
# module systemd._journal
# from /usr/lib/python3/dist-packages/systemd/_journal.cpython-36m-x86_64-linux-gnu.so
# by generator 1.147
# no doc
# no imports

# Variables with simple values

__version__ = '234'

# functions

def sendv(*args, **kwargs): # real signature unknown; NOTE: unreliably restored from __doc__ 
    """
    sendv('FIELD=value', 'FIELD=value', ...) -> None
    
    Send an entry to the journal.
    """
    pass

def stream_fd(identifier, priority, level_prefix): # real signature unknown; restored from __doc__
    """
    stream_fd(identifier, priority, level_prefix) -> fd
    
    Open a stream to journal by calling sd_journal_stream_fd(3).
    """
    pass

# no classes
# variables with complex values

__loader__ = None # (!) real value is '<_frozen_importlib_external.ExtensionFileLoader object at 0x7f09f34faac8>'

__spec__ = None # (!) real value is "ModuleSpec(name='systemd._journal', loader=<_frozen_importlib_external.ExtensionFileLoader object at 0x7f09f34faac8>, origin='/usr/lib/python3/dist-packages/systemd/_journal.cpython-36m-x86_64-linux-gnu.so')"

