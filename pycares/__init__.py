#!/usr/bin/env python

__version__ = '1.0.0'

try:
    from ._core import *
except ImportError:
    from ._cfficore import *
