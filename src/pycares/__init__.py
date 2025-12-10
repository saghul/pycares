
from ._cares import ffi as _ffi, lib as _lib
import _cffi_backend  # hint for bundler tools

if _lib.ARES_SUCCESS != _lib.ares_library_init(_lib.ARES_LIB_INIT_ALL) or _ffi is None:
    raise RuntimeError('Could not initialize c-ares')

if not _lib.ares_threadsafety():
    raise RuntimeError("c-ares is not built with thread safety")

from . import errno
from .utils import ascii_bytes, maybe_str, parse_name
from ._version import __version__

import math
import socket
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional, Dict, Union
from queue import SimpleQueue

IP4 = tuple[str, int]
IP6 = tuple[str, int, int, int]

# Flag values
ARES_FLAG_USEVC = _lib.ARES_FLAG_USEVC
ARES_FLAG_PRIMARY = _lib.ARES_FLAG_PRIMARY
ARES_FLAG_IGNTC = _lib.ARES_FLAG_IGNTC
ARES_FLAG_NORECURSE = _lib.ARES_FLAG_NORECURSE
ARES_FLAG_STAYOPEN = _lib.ARES_FLAG_STAYOPEN
ARES_FLAG_NOSEARCH = _lib.ARES_FLAG_NOSEARCH
ARES_FLAG_NOALIASES = _lib.ARES_FLAG_NOALIASES
ARES_FLAG_NOCHECKRESP = _lib.ARES_FLAG_NOCHECKRESP
ARES_FLAG_EDNS = _lib.ARES_FLAG_EDNS
ARES_FLAG_NO_DFLT_SVR = _lib.ARES_FLAG_NO_DFLT_SVR

# Nameinfo flag values
ARES_NI_NOFQDN = _lib.ARES_NI_NOFQDN
ARES_NI_NUMERICHOST = _lib.ARES_NI_NUMERICHOST
ARES_NI_NAMEREQD = _lib.ARES_NI_NAMEREQD
ARES_NI_NUMERICSERV = _lib.ARES_NI_NUMERICSERV
ARES_NI_DGRAM = _lib.ARES_NI_DGRAM
ARES_NI_TCP = _lib.ARES_NI_TCP
ARES_NI_UDP = _lib.ARES_NI_UDP
ARES_NI_SCTP = _lib.ARES_NI_SCTP
ARES_NI_DCCP = _lib.ARES_NI_DCCP
ARES_NI_NUMERICSCOPE = _lib.ARES_NI_NUMERICSCOPE
ARES_NI_LOOKUPHOST = _lib.ARES_NI_LOOKUPHOST
ARES_NI_LOOKUPSERVICE = _lib.ARES_NI_LOOKUPSERVICE
ARES_NI_IDN = _lib.ARES_NI_IDN
ARES_NI_IDN_ALLOW_UNASSIGNED = _lib.ARES_NI_IDN_ALLOW_UNASSIGNED
ARES_NI_IDN_USE_STD3_ASCII_RULES = _lib.ARES_NI_IDN_USE_STD3_ASCII_RULES

# Bad socket
ARES_SOCKET_BAD = _lib.ARES_SOCKET_BAD

# Query types
QUERY_TYPE_A = _lib.ARES_REC_TYPE_A
QUERY_TYPE_AAAA = _lib.ARES_REC_TYPE_AAAA
QUERY_TYPE_ANY = _lib.ARES_REC_TYPE_ANY
QUERY_TYPE_CAA = _lib.ARES_REC_TYPE_CAA
QUERY_TYPE_CNAME = _lib.ARES_REC_TYPE_CNAME
QUERY_TYPE_MX = _lib.ARES_REC_TYPE_MX
QUERY_TYPE_NAPTR = _lib.ARES_REC_TYPE_NAPTR
QUERY_TYPE_NS = _lib.ARES_REC_TYPE_NS
QUERY_TYPE_PTR = _lib.ARES_REC_TYPE_PTR
QUERY_TYPE_SOA = _lib.ARES_REC_TYPE_SOA
QUERY_TYPE_SRV = _lib.ARES_REC_TYPE_SRV
QUERY_TYPE_TXT = _lib.ARES_REC_TYPE_TXT
QUERY_TYPE_TLSA = _lib.ARES_REC_TYPE_TLSA
QUERY_TYPE_HTTPS = _lib.ARES_REC_TYPE_HTTPS
QUERY_TYPE_URI = _lib.ARES_REC_TYPE_URI

# Query classes
QUERY_CLASS_IN = _lib.ARES_CLASS_IN
QUERY_CLASS_CHAOS = _lib.ARES_CLASS_CHAOS
QUERY_CLASS_HS = _lib.ARES_CLASS_HESOID
QUERY_CLASS_NONE = _lib.ARES_CLASS_NONE
QUERY_CLASS_ANY = _lib.ARES_CLASS_ANY

ARES_VERSION = maybe_str(_ffi.string(_lib.ares_version(_ffi.NULL)))
PYCARES_ADDRTTL_SIZE = 256


class AresError(Exception):
    pass


# callback helpers

_handle_to_channel: Dict[Any, "Channel"] = {}  # Maps handle to channel to prevent use-after-free


@_ffi.def_extern()
def _sock_state_cb(data, socket_fd, readable, writable):
    # Note: sock_state_cb handle is not tracked in _handle_to_channel
    # because it has a different lifecycle (tied to the channel, not individual queries)
    sock_state_cb = _ffi.from_handle(data)
    sock_state_cb(socket_fd, readable, writable)

@_ffi.def_extern()
def _host_cb(arg, status, timeouts, hostent):
    # Get callback data without removing the reference yet
    if arg not in _handle_to_channel:
        return

    callback = _ffi.from_handle(arg)

    if status != _lib.ARES_SUCCESS:
        result = None
    else:
        result = parse_hostent(hostent)
        status = None

    callback(result, status)
    _handle_to_channel.pop(arg, None)

@_ffi.def_extern()
def _nameinfo_cb(arg, status, timeouts, node, service):
    # Get callback data without removing the reference yet
    if arg not in _handle_to_channel:
        return

    callback = _ffi.from_handle(arg)

    if status != _lib.ARES_SUCCESS:
        result = None
    else:
        result = parse_nameinfo(node, service)
        status = None

    callback(result, status)
    _handle_to_channel.pop(arg, None)

@_ffi.def_extern()
def _query_dnsrec_cb(arg, status, timeouts, dnsrec):
    """Callback for new DNS record API queries"""
    # Get callback data without removing the reference yet
    if arg not in _handle_to_channel:
        return

    callback = _ffi.from_handle(arg)

    if status != _lib.ARES_SUCCESS:
        result = None
    else:
        result, parse_status = parse_dnsrec(dnsrec)
        if parse_status is not None:
            status = parse_status
        else:
            # Success - set status to None
            status = None

    callback(result, status)
    _handle_to_channel.pop(arg, None)


@_ffi.def_extern()
def _addrinfo_cb(arg, status, timeouts, res):
    # Get callback data without removing the reference yet
    if arg not in _handle_to_channel:
        return

    callback = _ffi.from_handle(arg)

    if status != _lib.ARES_SUCCESS:
        result = None
    else:
        result = parse_addrinfo(res)
        status = None

    callback(result, status)
    _handle_to_channel.pop(arg, None)


def _extract_opt_params(rr, key):
    """Extract OPT params as list of (key, value) tuples for HTTPS/SVCB records."""
    opt_cnt = _lib.ares_dns_rr_get_opt_cnt(rr, key)
    if opt_cnt == 0:
        return []
    # Collect all options as a list of (key, value) tuples
    params = []
    for i in range(opt_cnt):
        val_ptr = _ffi.new("unsigned char **")
        val_len = _ffi.new("size_t *")
        opt_key = _lib.ares_dns_rr_get_opt(rr, key, i, val_ptr, val_len)
        if val_ptr[0] != _ffi.NULL:
            val = bytes(_ffi.buffer(val_ptr[0], val_len[0]))
        else:
            val = b''
        params.append((opt_key, val))
    return params


def extract_record_data(rr, record_type):
    """Extract type-specific data from a DNS resource record and return appropriate dataclass"""
    if record_type == _lib.ARES_REC_TYPE_A:
        addr = _lib.ares_dns_rr_get_addr(rr, _lib.ARES_RR_A_ADDR)
        buf = _ffi.new("char[]", _lib.INET6_ADDRSTRLEN)
        _lib.ares_inet_ntop(socket.AF_INET, addr, buf, _lib.INET6_ADDRSTRLEN)
        return ARecordData(addr=maybe_str(_ffi.string(buf)))

    elif record_type == _lib.ARES_REC_TYPE_AAAA:
        addr = _lib.ares_dns_rr_get_addr6(rr, _lib.ARES_RR_AAAA_ADDR)
        buf = _ffi.new("char[]", _lib.INET6_ADDRSTRLEN)
        _lib.ares_inet_ntop(socket.AF_INET6, addr, buf, _lib.INET6_ADDRSTRLEN)
        return AAAARecordData(addr=maybe_str(_ffi.string(buf)))

    elif record_type == _lib.ARES_REC_TYPE_MX:
        priority = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_MX_PREFERENCE)
        exchange = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_MX_EXCHANGE)
        return MXRecordData(priority=priority, exchange=maybe_str(_ffi.string(exchange)))

    elif record_type == _lib.ARES_REC_TYPE_TXT:
        # TXT records use ABIN (array of binary) for chunks
        cnt = _lib.ares_dns_rr_get_abin_cnt(rr, _lib.ARES_RR_TXT_DATA)
        chunks = []
        for i in range(cnt):
            length = _ffi.new("size_t *")
            data = _lib.ares_dns_rr_get_abin(rr, _lib.ARES_RR_TXT_DATA, i, length)
            if data != _ffi.NULL:
                chunks.append(_ffi.buffer(data, length[0])[:])
        return TXTRecordData(data=b''.join(chunks))

    elif record_type == _lib.ARES_REC_TYPE_CAA:
        critical = _lib.ares_dns_rr_get_u8(rr, _lib.ARES_RR_CAA_CRITICAL)
        tag = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_CAA_TAG)
        length = _ffi.new("size_t *")
        value = _lib.ares_dns_rr_get_bin(rr, _lib.ARES_RR_CAA_VALUE, length)
        value_str = maybe_str(_ffi.buffer(value, length[0])[:])
        return CAARecordData(critical=critical, tag=maybe_str(_ffi.string(tag)), value=value_str)

    elif record_type == _lib.ARES_REC_TYPE_CNAME:
        cname = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_CNAME_CNAME)
        return CNAMERecordData(cname=maybe_str(_ffi.string(cname)))

    elif record_type == _lib.ARES_REC_TYPE_NAPTR:
        order = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_NAPTR_ORDER)
        preference = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_NAPTR_PREFERENCE)
        flags = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_NAPTR_FLAGS)
        service = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_NAPTR_SERVICES)
        regexp = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_NAPTR_REGEXP)
        replacement = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_NAPTR_REPLACEMENT)
        return NAPTRRecordData(
            order=order,
            preference=preference,
            flags=maybe_str(_ffi.string(flags)),
            service=maybe_str(_ffi.string(service)),
            regexp=maybe_str(_ffi.string(regexp)),
            replacement=maybe_str(_ffi.string(replacement))
        )

    elif record_type == _lib.ARES_REC_TYPE_NS:
        nsdname = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_NS_NSDNAME)
        return NSRecordData(nsdname=maybe_str(_ffi.string(nsdname)))

    elif record_type == _lib.ARES_REC_TYPE_PTR:
        dname = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_PTR_DNAME)
        return PTRRecordData(dname=maybe_str(_ffi.string(dname)))

    elif record_type == _lib.ARES_REC_TYPE_SOA:
        mname = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_SOA_MNAME)
        rname = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_SOA_RNAME)
        serial = _lib.ares_dns_rr_get_u32(rr, _lib.ARES_RR_SOA_SERIAL)
        refresh = _lib.ares_dns_rr_get_u32(rr, _lib.ARES_RR_SOA_REFRESH)
        retry = _lib.ares_dns_rr_get_u32(rr, _lib.ARES_RR_SOA_RETRY)
        expire = _lib.ares_dns_rr_get_u32(rr, _lib.ARES_RR_SOA_EXPIRE)
        minimum = _lib.ares_dns_rr_get_u32(rr, _lib.ARES_RR_SOA_MINIMUM)
        return SOARecordData(
            mname=maybe_str(_ffi.string(mname)),
            rname=maybe_str(_ffi.string(rname)),
            serial=serial,
            refresh=refresh,
            retry=retry,
            expire=expire,
            minimum=minimum
        )

    elif record_type == _lib.ARES_REC_TYPE_SRV:
        priority = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_SRV_PRIORITY)
        weight = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_SRV_WEIGHT)
        port = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_SRV_PORT)
        target = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_SRV_TARGET)
        return SRVRecordData(
            priority=priority,
            weight=weight,
            port=port,
            target=maybe_str(_ffi.string(target))
        )

    elif record_type == _lib.ARES_REC_TYPE_TLSA:
        cert_usage = _lib.ares_dns_rr_get_u8(rr, _lib.ARES_RR_TLSA_CERT_USAGE)
        selector = _lib.ares_dns_rr_get_u8(rr, _lib.ARES_RR_TLSA_SELECTOR)
        matching_type = _lib.ares_dns_rr_get_u8(rr, _lib.ARES_RR_TLSA_MATCH)
        data_len = _ffi.new("size_t *")
        data_ptr = _lib.ares_dns_rr_get_bin(rr, _lib.ARES_RR_TLSA_DATA, data_len)
        cert_data = bytes(_ffi.buffer(data_ptr, data_len[0])) if data_ptr != _ffi.NULL else b''
        return TLSARecordData(
            cert_usage=cert_usage,
            selector=selector,
            matching_type=matching_type,
            cert_association_data=cert_data
        )

    elif record_type == _lib.ARES_REC_TYPE_HTTPS:
        priority = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_HTTPS_PRIORITY)
        target = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_HTTPS_TARGET)
        params = _extract_opt_params(rr, _lib.ARES_RR_HTTPS_PARAMS)
        return HTTPSRecordData(
            priority=priority,
            target=maybe_str(_ffi.string(target)),
            params=params
        )

    elif record_type == _lib.ARES_REC_TYPE_URI:
        priority = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_URI_PRIORITY)
        weight = _lib.ares_dns_rr_get_u16(rr, _lib.ARES_RR_URI_WEIGHT)
        target = _lib.ares_dns_rr_get_str(rr, _lib.ARES_RR_URI_TARGET)
        return URIRecordData(
            priority=priority,
            weight=weight,
            target=maybe_str(_ffi.string(target))
        )

    else:
        # Unknown record type - return None or raise error
        raise ValueError(f"Unsupported DNS record type: {record_type}")


def parse_dnsrec(dnsrec):
    """Parse ares_dns_record_t into DNSResult with all sections"""
    if dnsrec == _ffi.NULL:
        return None, _lib.ARES_EBADRESP

    answer_records = []
    authority_records = []
    additional_records = []

    # Parse answer section
    answer_count = _lib.ares_dns_record_rr_cnt(dnsrec, _lib.ARES_SECTION_ANSWER)
    for i in range(answer_count):
        rr = _lib.ares_dns_record_rr_get_const(dnsrec, _lib.ARES_SECTION_ANSWER, i)
        if rr != _ffi.NULL:
            name = maybe_str(_ffi.string(_lib.ares_dns_rr_get_name(rr)))
            rec_type = _lib.ares_dns_rr_get_type(rr)
            rec_class = _lib.ares_dns_rr_get_class(rr)
            ttl = _lib.ares_dns_rr_get_ttl(rr)

            try:
                data = extract_record_data(rr, rec_type)
                answer_records.append(DNSRecord(
                    name=name,
                    type=rec_type,
                    record_class=rec_class,
                    ttl=ttl,
                    data=data
                ))
            except (ValueError, Exception):
                # Skip unsupported record types
                pass

    # Parse authority section
    authority_count = _lib.ares_dns_record_rr_cnt(dnsrec, _lib.ARES_SECTION_AUTHORITY)
    for i in range(authority_count):
        rr = _lib.ares_dns_record_rr_get_const(dnsrec, _lib.ARES_SECTION_AUTHORITY, i)
        if rr != _ffi.NULL:
            name = maybe_str(_ffi.string(_lib.ares_dns_rr_get_name(rr)))
            rec_type = _lib.ares_dns_rr_get_type(rr)
            rec_class = _lib.ares_dns_rr_get_class(rr)
            ttl = _lib.ares_dns_rr_get_ttl(rr)

            try:
                data = extract_record_data(rr, rec_type)
                authority_records.append(DNSRecord(
                    name=name,
                    type=rec_type,
                    record_class=rec_class,
                    ttl=ttl,
                    data=data
                ))
            except (ValueError, Exception):
                # Skip unsupported record types
                pass

    # Parse additional section
    additional_count = _lib.ares_dns_record_rr_cnt(dnsrec, _lib.ARES_SECTION_ADDITIONAL)
    for i in range(additional_count):
        rr = _lib.ares_dns_record_rr_get_const(dnsrec, _lib.ARES_SECTION_ADDITIONAL, i)
        if rr != _ffi.NULL:
            name = maybe_str(_ffi.string(_lib.ares_dns_rr_get_name(rr)))
            rec_type = _lib.ares_dns_rr_get_type(rr)
            rec_class = _lib.ares_dns_rr_get_class(rr)
            ttl = _lib.ares_dns_rr_get_ttl(rr)

            try:
                data = extract_record_data(rr, rec_type)
                additional_records.append(DNSRecord(
                    name=name,
                    type=rec_type,
                    record_class=rec_class,
                    ttl=ttl,
                    data=data
                ))
            except (ValueError, Exception):
                # Skip unsupported record types
                pass

    result = DNSResult(
        answer=answer_records,
        authority=authority_records,
        additional=additional_records
    )

    return result, None


class _ChannelShutdownManager:
    """Manages channel destruction in a single background thread using SimpleQueue."""

    def __init__(self) -> None:
        self._queue: SimpleQueue = SimpleQueue()
        self._thread: Optional[threading.Thread] = None
        self._start_lock = threading.Lock()

    def _run_safe_shutdown_loop(self) -> None:
        """Process channel destruction requests from the queue."""
        while True:
            # Block forever until we get a channel to destroy
            channel, _ = self._queue.get()

            # Cancel all pending queries - this will trigger callbacks with ARES_ECANCELLED
            _lib.ares_cancel(channel[0])

            # Wait for all queries to finish
            _lib.ares_queue_wait_empty(channel[0], -1)

            # Destroy the channel
            if channel is not None:
                _lib.ares_destroy(channel[0])

    def start(self) -> None:
        """Start the background thread if not already started."""
        if self._thread is not None:
            return
        with self._start_lock:
            if self._thread is not None:
                # Started by another thread while waiting for the lock
                return
            self._thread = threading.Thread(target=self._run_safe_shutdown_loop, daemon=True)
            self._thread.start()

    def destroy_channel(self, channel, sock_state_cb_handle) -> None:
        """
        Schedule channel destruction on the background thread.

        The socket state callback handle is passed along to ensure it remains
        alive until the channel is destroyed.

        Thread Safety and Synchronization:
        This method uses SimpleQueue which is thread-safe for putting items
        from multiple threads. The background thread processes channels
        sequentially waiting for queries to end before each destruction.
        """
        self._queue.put((channel, sock_state_cb_handle))


# Global shutdown manager instance
_shutdown_manager = _ChannelShutdownManager()


class Channel:
    __qtypes__ = (_lib.ARES_REC_TYPE_A, _lib.ARES_REC_TYPE_AAAA, _lib.ARES_REC_TYPE_ANY, _lib.ARES_REC_TYPE_CAA, _lib.ARES_REC_TYPE_CNAME, _lib.ARES_REC_TYPE_HTTPS, _lib.ARES_REC_TYPE_MX, _lib.ARES_REC_TYPE_NAPTR, _lib.ARES_REC_TYPE_NS, _lib.ARES_REC_TYPE_PTR, _lib.ARES_REC_TYPE_SOA, _lib.ARES_REC_TYPE_SRV, _lib.ARES_REC_TYPE_TLSA, _lib.ARES_REC_TYPE_TXT, _lib.ARES_REC_TYPE_URI)
    __qclasses__ = (_lib.ARES_CLASS_IN, _lib.ARES_CLASS_CHAOS, _lib.ARES_CLASS_HESOID, _lib.ARES_CLASS_NONE, _lib.ARES_CLASS_ANY)

    def __init__(self,
                 *,
                 flags: Optional[int] = None,
                 timeout: Optional[float] = None,
                 tries: Optional[int] = None,
                 ndots: Optional[int] = None,
                 tcp_port: Optional[int] = None,
                 udp_port: Optional[int] = None,
                 servers: Optional[Iterable[Union[str, bytes]]] = None,
                 domains: Optional[Iterable[Union[str, bytes]]] = None,
                 lookups: Union[str, bytes, None] = None,
                 sock_state_cb: Optional[Callable[[int, bool, bool], None]] = None,
                 socket_send_buffer_size: Optional[int] = None,
                 socket_receive_buffer_size: Optional[int] = None,
                 rotate: bool = False,
                 local_ip: Union[str, bytes, None] = None,
                 local_dev: Optional[str] = None,
                 resolvconf_path: Union[str, bytes, None] = None) -> None:

        # Initialize _channel to None first to ensure __del__ doesn't fail
        self._channel = None

        # Store flags for later use (default is 0 if not specified)
        self._flags = flags if flags is not None else 0

        channel = _ffi.new("ares_channel *")
        options = _ffi.new("struct ares_options *")
        optmask = 0

        if flags is not None:
            options.flags = flags
            optmask = optmask | _lib.ARES_OPT_FLAGS

        if timeout is not None:
            options.timeout = int(timeout * 1000)
            optmask = optmask | _lib.ARES_OPT_TIMEOUTMS

        if tries is not None:
            options.tries = tries
            optmask = optmask |  _lib.ARES_OPT_TRIES

        if ndots is not None:
            options.ndots = ndots
            optmask = optmask |  _lib.ARES_OPT_NDOTS

        if tcp_port is not None:
            options.tcp_port = tcp_port
            optmask = optmask |  _lib.ARES_OPT_TCP_PORT

        if udp_port is not None:
            options.udp_port = udp_port
            optmask = optmask |  _lib.ARES_OPT_UDP_PORT

        if socket_send_buffer_size is not None:
            options.socket_send_buffer_size = socket_send_buffer_size
            optmask = optmask |  _lib.ARES_OPT_SOCK_SNDBUF

        if socket_receive_buffer_size is not None:
            options.socket_receive_buffer_size = socket_receive_buffer_size
            optmask = optmask |  _lib.ARES_OPT_SOCK_RCVBUF

        if sock_state_cb:
            if not callable(sock_state_cb):
                raise TypeError("sock_state_cb is not callable")

            userdata = _ffi.new_handle(sock_state_cb)

            # This must be kept alive while the channel is alive.
            self._sock_state_cb_handle = userdata

            options.sock_state_cb = _lib._sock_state_cb
            options.sock_state_cb_data = userdata
            optmask = optmask |  _lib.ARES_OPT_SOCK_STATE_CB
        else:
            self._sock_state_cb_handle = None
            optmask = optmask |  _lib.ARES_OPT_EVENT_THREAD
            options.evsys = _lib.ARES_EVSYS_DEFAULT

        if lookups:
            options.lookups = _ffi.new('char[]', ascii_bytes(lookups))
            optmask = optmask |  _lib.ARES_OPT_LOOKUPS

        if domains:
            strs = [_ffi.new("char[]", ascii_bytes(i)) for i in domains]
            c = _ffi.new("char *[%d]" % (len(domains) + 1))
            for i in range(len(domains)):
               c[i] = strs[i]

            options.domains = c
            options.ndomains = len(domains)
            optmask = optmask |  _lib.ARES_OPT_DOMAINS

        if rotate:
            optmask = optmask |  _lib.ARES_OPT_ROTATE

        if resolvconf_path is not None:
            optmask = optmask |  _lib.ARES_OPT_RESOLVCONF
            options.resolvconf_path = _ffi.new('char[]', ascii_bytes(resolvconf_path))

        r = _lib.ares_init_options(channel, options, optmask)
        if r != _lib.ARES_SUCCESS:
            raise AresError('Failed to initialize c-ares channel')

        self._channel = channel
        if servers:
            self.servers = servers

        if local_ip:
            self.set_local_ip(local_ip)

        if local_dev:
            self.set_local_dev(local_dev)

        # Ensure the shutdown thread is started
        _shutdown_manager.start()

    def __del__(self) -> None:
        """Ensure the channel is destroyed when the object is deleted."""
        self.close()

    def _create_callback_handle(self, callback_data):
        """
        Create a callback handle and register it for tracking.

        This ensures that:
        1. The callback data is wrapped in a CFFI handle
        2. The handle is mapped to this channel to keep it alive

        Args:
            callback_data: The data to pass to the callback (usually a callable or tuple)

        Returns:
            The CFFI handle that can be passed to C functions

        Raises:
            RuntimeError: If the channel is destroyed

        """
        if self._channel is None:
            raise RuntimeError("Channel is destroyed, no new queries allowed")

        userdata = _ffi.new_handle(callback_data)
        _handle_to_channel[userdata] = self
        return userdata

    def cancel(self) -> None:
        _lib.ares_cancel(self._channel[0])

    def reinit(self) -> None:
        r = _lib.ares_reinit(self._channel[0])
        if r != _lib.ARES_SUCCESS:
            raise AresError(r, errno.strerror(r))

    @property
    def servers(self) -> list[str]:
        csv_str = _lib.ares_get_servers_csv(self._channel[0])

        if csv_str == _ffi.NULL:
            raise AresError(_lib.ARES_ENOMEM, errno.strerror(_lib.ARES_ENOMEM))

        server_list = []
        csv_string = maybe_str(_ffi.string(csv_str))
        _lib.ares_free_string(csv_str)
        server_list = [s.strip() for s in csv_string.split(',')]

        return server_list

    @servers.setter
    def servers(self, servers: Iterable[Union[str, bytes]]) -> None:
        server_list = [ascii_bytes(s).decode('ascii') if isinstance(s, bytes) else s for s in servers]
        csv_str = ','.join(server_list)

        r = _lib.ares_set_servers_csv(self._channel[0], csv_str.encode('ascii'))
        if r != _lib.ARES_SUCCESS:
            raise AresError(r, errno.strerror(r))

    def process_fd(self, read_fd: int, write_fd: int) -> None:
        _lib.ares_process_fd(self._channel[0], _ffi.cast("ares_socket_t", read_fd), _ffi.cast("ares_socket_t", write_fd))

    def process_read_fd(self, read_fd:int) -> None:
        _lib.ares_process_fd(self._channel[0], _ffi.cast("ares_socket_t", read_fd), _ffi.cast("ares_socket_t", ARES_SOCKET_BAD))

    def process_write_fd(self, write_fd:int) -> None:
        _lib.ares_process_fd(self._channel[0], _ffi.cast("ares_socket_t", ARES_SOCKET_BAD), _ffi.cast("ares_socket_t", write_fd))

    def timeout(self, t = None):
        maxtv = _ffi.NULL
        tv = _ffi.new("struct timeval*")

        if t is not None:
            if t >= 0.0:
                maxtv = _ffi.new("struct timeval*")
                maxtv.tv_sec = int(math.floor(t))
                maxtv.tv_usec = int(math.fmod(t, 1.0) * 1000000)
            else:
                raise ValueError("timeout needs to be a positive number or None")

        _lib.ares_timeout(self._channel[0], maxtv, tv)

        if tv == _ffi.NULL:
            return 0.0

        return (tv.tv_sec + tv.tv_usec / 1000000.0)

    def gethostbyaddr(self, addr: str, *, callback: Callable[[Any, int], None]) -> None:
        if not callable(callback):
            raise TypeError("a callable is required")

        addr4 = _ffi.new("struct in_addr*")
        addr6 = _ffi.new("struct ares_in6_addr*")
        if _lib.ares_inet_pton(socket.AF_INET, ascii_bytes(addr), (addr4)) == 1:
            address = addr4
            family = socket.AF_INET
        elif _lib.ares_inet_pton(socket.AF_INET6, ascii_bytes(addr), (addr6)) == 1:
            address = addr6
            family = socket.AF_INET6
        else:
            raise ValueError("invalid IP address")

        userdata = self._create_callback_handle(callback)
        _lib.ares_gethostbyaddr(self._channel[0], address, _ffi.sizeof(address[0]), family, _lib._host_cb, userdata)

    def getaddrinfo(
        self,
        host: str,
        port: Optional[int],
        *,
        family: socket.AddressFamily = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0,
        callback: Callable[[Any, int], None]
    ) -> None:
        if not callable(callback):
            raise TypeError("a callable is required")

        if port is None:
            service = _ffi.NULL
        elif isinstance(port, int):
            service = str(port).encode('ascii')
        else:
            service = ascii_bytes(port)

        userdata = self._create_callback_handle(callback)

        hints = _ffi.new('struct ares_addrinfo_hints*')
        hints.ai_flags = flags
        hints.ai_family = family
        hints.ai_socktype = type
        hints.ai_protocol = proto
        _lib.ares_getaddrinfo(self._channel[0], parse_name(host), service, hints, _lib._addrinfo_cb, userdata)

    def query(self, name: str, query_type: int, *, query_class: int = QUERY_CLASS_IN, callback: Callable[[Any, int], None]) -> None:
        """
        Perform a DNS query.

        Args:
            name: Domain name to query
            query_type: Type of query (e.g., QUERY_TYPE_A, QUERY_TYPE_AAAA, etc.)
            query_class: Query class (default: QUERY_CLASS_IN)
            callback: Callback function that receives (result, errno)

        The callback will receive a DNSResult object containing answer, authority, and additional sections.
        """
        if not callable(callback):
            raise TypeError('a callable is required')

        if query_type not in self.__qtypes__:
            raise ValueError('invalid query type specified')

        if query_class not in self.__qclasses__:
            raise ValueError('invalid query class specified')

        userdata = self._create_callback_handle(callback)
        qid = _ffi.new("unsigned short *")
        status = _lib.ares_query_dnsrec(
            self._channel[0],
            parse_name(name),
            query_class,
            query_type,
            _lib._query_dnsrec_cb,
            userdata,
            qid
        )
        if status != _lib.ARES_SUCCESS:
            _handle_to_channel.pop(userdata, None)
            raise AresError(status, errno.strerror(status))

    def search(self, name: str, query_type: int, *, query_class: int = QUERY_CLASS_IN, callback: Callable[[Any, int], None]) -> None:
        """
        Perform a DNS search (honors resolv.conf search domains).

        Args:
            name: Domain name to search
            query_type: Type of query (e.g., QUERY_TYPE_A, QUERY_TYPE_AAAA, etc.)
            query_class: Query class (default: QUERY_CLASS_IN)
            callback: Callback function that receives (result, errno)

        The callback will receive a DNSResult object containing answer, authority, and additional sections.
        """
        if not callable(callback):
            raise TypeError('a callable is required')

        if query_type not in self.__qtypes__:
            raise ValueError('invalid query type specified')

        if query_class not in self.__qclasses__:
            raise ValueError('invalid query class specified')

        # Create a DNS record for the search query
        # Set RD (Recursion Desired) flag unless ARES_FLAG_NORECURSE is set
        dns_flags = 0 if (self._flags & _lib.ARES_FLAG_NORECURSE) else _lib.ARES_FLAG_RD

        dnsrec_p = _ffi.new("ares_dns_record_t **")
        status = _lib.ares_dns_record_create(
            dnsrec_p,
            0,  # id (will be set by c-ares)
            dns_flags,  # flags - include RD for recursive queries
            _lib.ARES_OPCODE_QUERY,
            _lib.ARES_RCODE_NOERROR
        )
        if status != _lib.ARES_SUCCESS:
            raise AresError(status, errno.strerror(status))

        dnsrec = dnsrec_p[0]

        # Add the query to the DNS record
        status = _lib.ares_dns_record_query_add(
            dnsrec,
            parse_name(name),
            query_type,
            query_class
        )
        if status != _lib.ARES_SUCCESS:
            _lib.ares_dns_record_destroy(dnsrec)
            raise AresError(status, errno.strerror(status))

        # Wrap callback to destroy DNS record after it's called
        original_callback = callback
        def cleanup_callback(result, error):
            try:
                original_callback(result, error)
            finally:
                # Clean up the DNS record after the callback completes
                _lib.ares_dns_record_destroy(dnsrec)

        # Perform the search with the created DNS record
        userdata = self._create_callback_handle(cleanup_callback)
        status = _lib.ares_search_dnsrec(
            self._channel[0],
            dnsrec,
            _lib._query_dnsrec_cb,
            userdata
        )
        if status != _lib.ARES_SUCCESS:
            _handle_to_channel.pop(userdata, None)
            _lib.ares_dns_record_destroy(dnsrec)
            raise AresError(status, errno.strerror(status))

    def set_local_ip(self, ip):
        addr4 = _ffi.new("struct in_addr*")
        addr6 = _ffi.new("struct ares_in6_addr*")
        if _lib.ares_inet_pton(socket.AF_INET, ascii_bytes(ip), addr4) == 1:
            _lib.ares_set_local_ip4(self._channel[0], socket.ntohl(addr4.s_addr))
        elif _lib.ares_inet_pton(socket.AF_INET6, ascii_bytes(ip), addr6) == 1:
            _lib.ares_set_local_ip6(self._channel[0], addr6)
        else:
            raise ValueError("invalid IP address")

    def getnameinfo(self, address: Union[IP4, IP6], flags: int, *, callback: Callable[[Any, int], None]) -> None:
        if not callable(callback):
            raise TypeError("a callable is required")

        if len(address) == 2:
            (ip, port) = address
            sa4 = _ffi.new("struct sockaddr_in*")
            if _lib.ares_inet_pton(socket.AF_INET, ascii_bytes(ip), _ffi.addressof(sa4.sin_addr)) != 1:
                raise ValueError("Invalid IPv4 address %r" % ip)
            sa4.sin_family = socket.AF_INET
            sa4.sin_port = socket.htons(port)
            sa = sa4
        elif len(address) == 4:
            (ip, port, flowinfo, scope_id) = address
            sa6 = _ffi.new("struct sockaddr_in6*")
            if _lib.ares_inet_pton(socket.AF_INET6, ascii_bytes(ip), _ffi.addressof(sa6.sin6_addr)) != 1:
                raise ValueError("Invalid IPv6 address %r" % ip)
            sa6.sin6_family = socket.AF_INET6
            sa6.sin6_port = socket.htons(port)
            sa6.sin6_flowinfo = socket.htonl(flowinfo) # I'm unsure about byteorder here.
            sa6.sin6_scope_id = scope_id # Yes, without htonl.
            sa = sa6
        else:
            raise ValueError("Invalid address argument")

        userdata = self._create_callback_handle(callback)
        _lib.ares_getnameinfo(self._channel[0], _ffi.cast("struct sockaddr*", sa), _ffi.sizeof(sa[0]), flags, _lib._nameinfo_cb, userdata)

    def set_local_dev(self, dev):
        _lib.ares_set_local_dev(self._channel[0], dev)

    def close(self) -> None:
        """
        Close the channel as soon as it's safe to do so.

        This method can be called from any thread. The channel will be destroyed
        safely using a background thread with a 1-second delay to ensure c-ares
        has completed its cleanup.

        Note: Once close() is called, no new queries can be started. Any pending
        queries will be cancelled and their callbacks will receive ARES_ECANCELLED.

        """
        if self._channel is None:
            # Already destroyed
            return

        # NB: don't cancel queries here, it may lead to problem if done from a
        # query callback.

        # Schedule channel destruction
        channel, self._channel = self._channel, None
        _shutdown_manager.destroy_channel(channel, self._sock_state_cb_handle)

    def wait(self, timeout: float=None) -> bool:
        """
        Wait until all pending queries are complete or timeout occurs.

        Args:
            timeout: Maximum time to wait in seconds. Use -1 for infinite wait.
        """
        r = _lib.ares_queue_wait_empty(self._channel[0],  int(timeout * 1000) if timeout is not None and timeout >= 0 else -1)
        if r == _lib.ARES_SUCCESS:
            return True
        elif r == _lib.ARES_ETIMEOUT:
            return False
        else:
            raise AresError(r, errno.strerror(r))


# DNS query result types - New dataclass-based API
#

@dataclass
class ARecordData:
    """Data for A (IPv4 address) record"""
    addr: str

@dataclass
class AAAARecordData:
    """Data for AAAA (IPv6 address) record"""
    addr: str

@dataclass
class MXRecordData:
    """Data for MX (mail exchange) record"""
    priority: int
    exchange: str

@dataclass
class TXTRecordData:
    """Data for TXT (text) record"""
    data: bytes

@dataclass
class CAARecordData:
    """Data for CAA (certification authority authorization) record"""
    critical: int
    tag: str
    value: str

@dataclass
class CNAMERecordData:
    """Data for CNAME (canonical name) record"""
    cname: str

@dataclass
class NAPTRRecordData:
    """Data for NAPTR (naming authority pointer) record"""
    order: int
    preference: int
    flags: str
    service: str
    regexp: str
    replacement: str

@dataclass
class NSRecordData:
    """Data for NS (name server) record"""
    nsdname: str

@dataclass
class PTRRecordData:
    """Data for PTR (pointer) record"""
    dname: str

@dataclass
class SOARecordData:
    """Data for SOA (start of authority) record"""
    mname: str
    rname: str
    serial: int
    refresh: int
    retry: int
    expire: int
    minimum: int

@dataclass
class SRVRecordData:
    """Data for SRV (service) record"""
    priority: int
    weight: int
    port: int
    target: str

@dataclass
class TLSARecordData:
    """Data for TLSA (DANE TLS authentication) record - RFC 6698"""
    cert_usage: int
    selector: int
    matching_type: int
    cert_association_data: bytes

@dataclass
class HTTPSRecordData:
    """Data for HTTPS (service binding) record - RFC 9460"""
    priority: int
    target: str
    params: list  # List of (key: int, value: bytes) tuples

@dataclass
class URIRecordData:
    """Data for URI (Uniform Resource Identifier) record - RFC 7553"""
    priority: int
    weight: int
    target: str

@dataclass
class DNSRecord:
    """Represents a single DNS resource record"""
    name: str
    type: int
    record_class: int
    ttl: int
    data: Union[ARecordData, AAAARecordData, MXRecordData, TXTRecordData,
                CAARecordData, CNAMERecordData, HTTPSRecordData, NAPTRRecordData,
                NSRecordData, PTRRecordData, SOARecordData, SRVRecordData,
                TLSARecordData, URIRecordData]

@dataclass
class DNSResult:
    """Represents a complete DNS query result with all sections"""
    answer: list[DNSRecord]
    authority: list[DNSRecord]
    additional: list[DNSRecord]


# Host/AddrInfo result types

@dataclass
class HostResult:
    """Result from gethostbyaddr() operation"""
    name: str
    aliases: list[str]
    addresses: list[str]

@dataclass
class NameInfoResult:
    """Result from getnameinfo() operation"""
    node: str
    service: Optional[str]

@dataclass
class AddrInfoNode:
    """Single address node from getaddrinfo() result"""
    ttl: int
    flags: int
    family: int
    socktype: int
    protocol: int
    addr: tuple  # (ip, port) or (ip, port, flowinfo, scope_id)

@dataclass
class AddrInfoCname:
    """CNAME information from getaddrinfo() result"""
    ttl: int
    alias: str
    name: str

@dataclass
class AddrInfoResult:
    """Complete result from getaddrinfo() operation"""
    cnames: list[AddrInfoCname]
    nodes: list[AddrInfoNode]


# Parser functions for Host/AddrInfo results

def parse_hostent(hostent) -> HostResult:
    """Parse c-ares hostent structure into HostResult"""
    name = maybe_str(_ffi.string(hostent.h_name))
    aliases = []
    addresses = []

    i = 0
    while hostent.h_aliases[i] != _ffi.NULL:
        aliases.append(maybe_str(_ffi.string(hostent.h_aliases[i])))
        i += 1

    i = 0
    while hostent.h_addr_list[i] != _ffi.NULL:
        buf = _ffi.new("char[]", _lib.INET6_ADDRSTRLEN)
        if _ffi.NULL != _lib.ares_inet_ntop(hostent.h_addrtype, hostent.h_addr_list[i], buf, _lib.INET6_ADDRSTRLEN):
            addresses.append(maybe_str(_ffi.string(buf, _lib.INET6_ADDRSTRLEN)))
        i += 1

    return HostResult(name=name, aliases=aliases, addresses=addresses)


def parse_nameinfo(node, service) -> NameInfoResult:
    """Parse c-ares nameinfo into NameInfoResult"""
    node_str = maybe_str(_ffi.string(node))
    service_str = maybe_str(_ffi.string(service)) if service != _ffi.NULL else None
    return NameInfoResult(node=node_str, service=service_str)


def parse_addrinfo_node(ares_node) -> AddrInfoNode:
    """Parse a single c-ares addrinfo node into AddrInfoNode"""
    ttl = ares_node.ai_ttl
    flags = ares_node.ai_flags
    socktype = ares_node.ai_socktype
    protocol = ares_node.ai_protocol

    addr_struct = ares_node.ai_addr
    assert addr_struct.sa_family == ares_node.ai_family
    ip = _ffi.new("char []", _lib.INET6_ADDRSTRLEN)

    if addr_struct.sa_family == socket.AF_INET:
        family = socket.AF_INET
        s = _ffi.cast("struct sockaddr_in*", addr_struct)
        if _ffi.NULL != _lib.ares_inet_ntop(s.sin_family, _ffi.addressof(s.sin_addr), ip, _lib.INET6_ADDRSTRLEN):
            # (address, port) 2-tuple for AF_INET
            addr = (_ffi.string(ip, _lib.INET6_ADDRSTRLEN), socket.ntohs(s.sin_port))
        else:
            raise ValueError("failed to convert IPv4 address")
    elif addr_struct.sa_family == socket.AF_INET6:
        family = socket.AF_INET6
        s = _ffi.cast("struct sockaddr_in6*", addr_struct)
        if _ffi.NULL != _lib.ares_inet_ntop(s.sin6_family, _ffi.addressof(s.sin6_addr), ip, _lib.INET6_ADDRSTRLEN):
            # (address, port, flow info, scope id) 4-tuple for AF_INET6
            addr = (_ffi.string(ip, _lib.INET6_ADDRSTRLEN), socket.ntohs(s.sin6_port), s.sin6_flowinfo, s.sin6_scope_id)
        else:
            raise ValueError("failed to convert IPv6 address")
    else:
        raise ValueError("invalid sockaddr family")

    return AddrInfoNode(ttl=ttl, flags=flags, family=family, socktype=socktype, protocol=protocol, addr=addr)


def parse_addrinfo_cname(ares_cname) -> AddrInfoCname:
    """Parse a single c-ares addrinfo cname into AddrInfoCname"""
    return AddrInfoCname(
        ttl=ares_cname.ttl,
        alias=maybe_str(_ffi.string(ares_cname.alias)),
        name=maybe_str(_ffi.string(ares_cname.name))
    )


def parse_addrinfo(ares_addrinfo) -> AddrInfoResult:
    """Parse c-ares addrinfo structure into AddrInfoResult"""
    cnames = []
    nodes = []

    cname_ptr = ares_addrinfo.cnames
    while cname_ptr != _ffi.NULL:
        cnames.append(parse_addrinfo_cname(cname_ptr))
        cname_ptr = cname_ptr.next

    node_ptr = ares_addrinfo.nodes
    while node_ptr != _ffi.NULL:
        nodes.append(parse_addrinfo_node(node_ptr))
        node_ptr = node_ptr.ai_next

    _lib.ares_freeaddrinfo(ares_addrinfo)

    return AddrInfoResult(cnames=cnames, nodes=nodes)


__all__ = (
    # Channel flags
    "ARES_FLAG_USEVC",
    "ARES_FLAG_PRIMARY",
    "ARES_FLAG_IGNTC",
    "ARES_FLAG_NORECURSE",
    "ARES_FLAG_STAYOPEN",
    "ARES_FLAG_NOSEARCH",
    "ARES_FLAG_NOALIASES",
    "ARES_FLAG_NOCHECKRESP",
    "ARES_FLAG_EDNS",
    "ARES_FLAG_NO_DFLT_SVR",

    # Nameinfo flag values
    "ARES_NI_NOFQDN",
    "ARES_NI_NUMERICHOST",
    "ARES_NI_NAMEREQD",
    "ARES_NI_NUMERICSERV",
    "ARES_NI_DGRAM",
    "ARES_NI_TCP",
    "ARES_NI_UDP",
    "ARES_NI_SCTP",
    "ARES_NI_DCCP",
    "ARES_NI_NUMERICSCOPE",
    "ARES_NI_LOOKUPHOST",
    "ARES_NI_LOOKUPSERVICE",
    "ARES_NI_IDN",
    "ARES_NI_IDN_ALLOW_UNASSIGNED",
    "ARES_NI_IDN_USE_STD3_ASCII_RULES",

    # Bad socket
    "ARES_SOCKET_BAD",

    # Query types
    "QUERY_TYPE_A",
    "QUERY_TYPE_AAAA",
    "QUERY_TYPE_ANY",
    "QUERY_TYPE_CAA",
    "QUERY_TYPE_CNAME",
    "QUERY_TYPE_HTTPS",
    "QUERY_TYPE_MX",
    "QUERY_TYPE_NAPTR",
    "QUERY_TYPE_NS",
    "QUERY_TYPE_PTR",
    "QUERY_TYPE_SOA",
    "QUERY_TYPE_SRV",
    "QUERY_TYPE_TLSA",
    "QUERY_TYPE_TXT",
    "QUERY_TYPE_URI",

    # Query classes
    "QUERY_CLASS_IN",
    "QUERY_CLASS_CHAOS",
    "QUERY_CLASS_HS",
    "QUERY_CLASS_NONE",
    "QUERY_CLASS_ANY",

    # Core stuff
    "ARES_VERSION",
    "AresError",
    "Channel",
    "errno",
    "__version__",

    # DNS record result types
    "DNSResult",
    "DNSRecord",
    "ARecordData",
    "AAAARecordData",
    "MXRecordData",
    "TXTRecordData",
    "CAARecordData",
    "CNAMERecordData",
    "HTTPSRecordData",
    "NAPTRRecordData",
    "NSRecordData",
    "PTRRecordData",
    "SOARecordData",
    "SRVRecordData",
    "TLSARecordData",
    "URIRecordData",

    # Host/AddrInfo result types
    "HostResult",
    "NameInfoResult",
    "AddrInfoResult",
    "AddrInfoNode",
    "AddrInfoCname",
)
