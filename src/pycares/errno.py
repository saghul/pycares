from typing import Union

from ._cares import ffi as _ffi, lib as _lib
from .utils import maybe_str

errorcode = {}

ARES_SUCCESS = errorcode[_lib.ARES_SUCCESS] = "ARES_SUCCESS"
# error codes
ARES_ENODATA = errorcode[_lib.ARES_ENODATA] = "ARES_ENODATA"
ARES_EFORMERR = errorcode[_lib.ARES_EFORMERR] = "ARES_EFORMERR"
ARES_ESERVFAIL = errorcode[_lib.ARES_ESERVFAIL] = "ARES_ESERVFAIL"
ARES_ENOTFOUND = errorcode[_lib.ARES_ENOTFOUND] = "ARES_ENOTFOUND"
ARES_ENOTIMP = errorcode[_lib.ARES_ENOTIMP] = "ARES_ENOTIMP"
ARES_EREFUSED = errorcode[_lib.ARES_EREFUSED] = "ARES_EREFUSED"
ARES_EBADQUERY = errorcode[_lib.ARES_EBADQUERY] = "ARES_EBADQUERY"
ARES_EBADNAME = errorcode[_lib.ARES_EBADNAME] = "ARES_EBADNAME"
ARES_EBADFAMILY = errorcode[_lib.ARES_EBADFAMILY] = "ARES_EBADFAMILY"
ARES_EBADRESP = errorcode[_lib.ARES_EBADRESP] = "ARES_EBADRESP"
ARES_ECONNREFUSED = errorcode[_lib.ARES_ECONNREFUSED] = "ARES_ECONNREFUSED"
ARES_ETIMEOUT = errorcode[_lib.ARES_ETIMEOUT] = "ARES_ETIMEOUT"
ARES_EOF = errorcode[_lib.ARES_EOF] = "ARES_EOF"
ARES_EFILE = errorcode[_lib.ARES_EFILE] = "ARES_EFILE"
ARES_ENOMEM = errorcode[_lib.ARES_ENOMEM] = "ARES_ENOMEM"
ARES_EDESTRUCTION = errorcode[_lib.ARES_EDESTRUCTION] = "ARES_EDESTRUCTION"
ARES_EBADSTR = errorcode[_lib.ARES_EBADSTR] = "ARES_EBADSTR"
ARES_EBADFLAGS = errorcode[_lib.ARES_EBADFLAGS] = "ARES_EBADFLAGS"
ARES_ENONAME = errorcode[_lib.ARES_ENONAME] = "ARES_ENONAME"
ARES_EBADHINTS = errorcode[_lib.ARES_EBADHINTS] = "ARES_EBADHINTS"
ARES_ENOTINITIALIZED = errorcode[_lib.ARES_ENOTINITIALIZED] = "ARES_ENOTINITIALIZED"
ARES_ELOADIPHLPAPI = errorcode[_lib.ARES_ELOADIPHLPAPI] = "ARES_ELOADIPHLPAPI"
ARES_EADDRGETNETWORKPARAMS = errorcode[_lib.ARES_EADDRGETNETWORKPARAMS] = "ARES_EADDRGETNETWORKPARAMS"
ARES_ECANCELLED = errorcode[_lib.ARES_ECANCELLED] = "ARES_ECANCELLED"
ARES_ESERVICE = errorcode[_lib.ARES_ESERVICE] = "ARES_ESERVICE"


def strerror(code: int) -> Union[str, bytes]:
    return maybe_str(_ffi.string(_lib.ares_strerror(code)))


__all__ = ("errorcode", "strerror", *errorcode.keys())
