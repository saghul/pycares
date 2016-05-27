
try:
    from ._core.errno import *
except ImportError:
    from ._cfficore.errno import *
