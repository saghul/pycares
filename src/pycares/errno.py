from typing import Union

from ._cares import ffi as _ffi, lib as _lib
from .utils import maybe_str

errorcode = {}

ARES_SUCCESS = errorcode["ARES_SUCCESS"] = _lib.ARES_SUCCESS
# error codes
ARES_ENODATA = errorcode["ARES_ENODATA"] = _lib.ARES_ENODATA
ARES_EFORMERR = errorcode["ARES_EFORMERR"] = _lib.ARES_EFORMERR
ARES_ESERVFAIL = errorcode["ARES_ESERVFAIL"] = _lib.ARES_ESERVFAIL
ARES_ENOTFOUND = errorcode["ARES_ENOTFOUND"] = _lib.ARES_ENOTFOUND
ARES_ENOTIMP = errorcode["ARES_ENOTIMP"] = _lib.ARES_ENOTIMP
ARES_EREFUSED = errorcode["ARES_EREFUSED"] = _lib.ARES_EREFUSED
ARES_EBADQUERY = errorcode["ARES_EBADQUERY"] = _lib.ARES_EBADQUERY
ARES_EBADNAME = errorcode["ARES_EBADNAME"] = _lib.ARES_EBADNAME
ARES_EBADFAMILY = errorcode["ARES_EBADFAMILY"] = _lib.ARES_EBADFAMILY
ARES_EBADRESP = errorcode["ARES_EBADRESP"] = _lib.ARES_EBADRESP
ARES_ECONNREFUSED = errorcode["ARES_ECONNREFUSED"] = _lib.ARES_ECONNREFUSED
ARES_ETIMEOUT = errorcode["ARES_ETIMEOUT"] = _lib.ARES_ETIMEOUT
ARES_EOF = errorcode["ARES_EOF"] = _lib.ARES_EOF
ARES_EFILE = errorcode["ARES_EFILE"] = _lib.ARES_EFILE
ARES_ENOMEM = errorcode["ARES_ENOMEM"] = _lib.ARES_ENOMEM
ARES_EDESTRUCTION = errorcode["ARES_EDESTRUCTION"] = _lib.ARES_EDESTRUCTION
ARES_EBADSTR = errorcode["ARES_EBADSTR"] = _lib.ARES_EBADSTR
ARES_EBADFLAGS = errorcode["ARES_EBADFLAGS"] = _lib.ARES_EBADFLAGS
ARES_ENONAME = errorcode["ARES_ENONAME"] = _lib.ARES_ENONAME
ARES_EBADHINTS = errorcode["ARES_EBADHINTS"] = _lib.ARES_EBADHINTS
ARES_ENOTINITIALIZED = errorcode["ARES_ENOTINITIALIZED"] = _lib.ARES_ENOTINITIALIZED
ARES_ELOADIPHLPAPI = errorcode["ARES_ELOADIPHLPAPI"] = _lib.ARES_ELOADIPHLPAPI
ARES_EADDRGETNETWORKPARAMS = errorcode["ARES_EADDRGETNETWORKPARAMS"] = _lib.ARES_EADDRGETNETWORKPARAMS
ARES_ECANCELLED = errorcode["ARES_ECANCELLED"] = _lib.ARES_ECANCELLED
ARES_ESERVICE = errorcode["ARES_ESERVICE"] = _lib.ARES_ESERVICE


def strerror(code: int) -> Union[str, bytes]:
    return maybe_str(_ffi.string(_lib.ares_strerror(code)))


__all__ = ("errorcode", "strerror", *errorcode.keys())
