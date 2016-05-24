
from ._version import __version__

try:
    from ._core import *
except ImportError:
    from ._cfficore import *
