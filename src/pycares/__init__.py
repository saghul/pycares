
from ._cares import ffi as _ffi, lib as _lib
import _cffi_backend  # hint for bundler tools

if _lib.ARES_SUCCESS != _lib.ares_library_init(_lib.ARES_LIB_INIT_ALL) or _ffi is None:
    raise RuntimeError('Could not initialize c-ares')

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
        result = ares_host_result(hostent)
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
        result = ares_nameinfo_result(node, service)
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
        result = ares_addrinfo_result(res)
        status = None

    callback(result, status)
    _handle_to_channel.pop(arg, None)


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
        text = b''.join(chunks).decode('utf-8', errors='replace')
        return TXTRecordData(text=text)

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
            channel = self._queue.get()

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

    def destroy_channel(self, channel) -> None:
        """
        Schedule channel destruction on the background thread with a safety delay.

        Thread Safety and Synchronization:
        This method uses SimpleQueue which is thread-safe for putting items
        from multiple threads. The background thread processes channels
        sequentially waiting for queries to end before each destruction.
        """
        self._queue.put(channel)


# Global shutdown manager instance
_shutdown_manager = _ChannelShutdownManager()


class Channel:
    __qtypes__ = (_lib.ARES_REC_TYPE_A, _lib.ARES_REC_TYPE_AAAA, _lib.ARES_REC_TYPE_ANY, _lib.ARES_REC_TYPE_CAA, _lib.ARES_REC_TYPE_CNAME, _lib.ARES_REC_TYPE_MX, _lib.ARES_REC_TYPE_NAPTR, _lib.ARES_REC_TYPE_NS, _lib.ARES_REC_TYPE_PTR, _lib.ARES_REC_TYPE_SOA, _lib.ARES_REC_TYPE_SRV, _lib.ARES_REC_TYPE_TXT)
    __qclasses__ = (_lib.ARES_CLASS_IN, _lib.ARES_CLASS_CHAOS, _lib.ARES_CLASS_HESOID, _lib.ARES_CLASS_NONE, _lib.ARES_CLASS_ANY)

    def __init__(self,
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
                 resolvconf_path: Union[str, bytes, None] = None,
                 event_thread: bool = False) -> None:

        # Initialize _channel to None first to ensure __del__ doesn't fail
        self._channel = None

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
            if event_thread:
                raise RuntimeError("sock_state_cb and event_thread cannot be used together")

            userdata = _ffi.new_handle(sock_state_cb)

            # This must be kept alive while the channel is alive.
            self._sock_state_cb_handle = userdata

            options.sock_state_cb = _lib._sock_state_cb
            options.sock_state_cb_data = userdata
            optmask = optmask |  _lib.ARES_OPT_SOCK_STATE_CB

        if event_thread:
            if not ares_threadsafety():
                raise RuntimeError("c-ares is not built with thread safety")
            if sock_state_cb:
                raise RuntimeError("sock_state_cb and event_thread cannot be used together")
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

        # Initialize all attributes for consistency
        self._event_thread = event_thread
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

    def gethostbyaddr(self, addr: str, callback: Callable[[Any, int], None]) -> None:
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
        callback: Callable[[Any, int], None],
        family: socket.AddressFamily = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0
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

    def query(self, name: str, query_type: str, callback: Callable[[Any, int], None], query_class: Optional[str] = None) -> None:
        """
        Perform a DNS query.

        Args:
            name: Domain name to query
            query_type: Type of query (e.g., QUERY_TYPE_A, QUERY_TYPE_AAAA, etc.)
            callback: Callback function that receives (result, errno)
            query_class: Query class (default: QUERY_CLASS_IN)

        The callback will receive a DNSResult object containing answer, authority, and additional sections.
        """
        if not callable(callback):
            raise TypeError('a callable is required')

        if query_type not in self.__qtypes__:
            raise ValueError('invalid query type specified')

        if query_class is None:
            query_class = _lib.ARES_CLASS_IN
        elif query_class not in self.__qclasses__:
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

    def search(self, name, query_type, callback, query_class=None):
        """
        Perform a DNS search (honors resolv.conf search domains).

        Args:
            name: Domain name to search
            query_type: Type of query (e.g., QUERY_TYPE_A, QUERY_TYPE_AAAA, etc.)
            callback: Callback function that receives (result, errno)
            query_class: Query class (default: QUERY_CLASS_IN)

        The callback will receive a DNSResult object containing answer, authority, and additional sections.
        """
        if not callable(callback):
            raise TypeError('a callable is required')

        if query_type not in self.__qtypes__:
            raise ValueError('invalid query type specified')

        if query_class is None:
            query_class = _lib.ARES_CLASS_IN
        elif query_class not in self.__qclasses__:
            raise ValueError('invalid query class specified')

        # Create a DNS record for the search query
        dnsrec_p = _ffi.new("ares_dns_record_t **")
        status = _lib.ares_dns_record_create(
            dnsrec_p,
            0,  # id (will be set by c-ares)
            0,  # flags
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

    def getnameinfo(self, address: Union[IP4, IP6], flags: int, callback: Callable[[Any, int], None]) -> None:
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
        _shutdown_manager.destroy_channel(channel)

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
    text: str

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
class DNSRecord:
    """Represents a single DNS resource record"""
    name: str
    type: int
    record_class: int
    ttl: int
    data: Union[ARecordData, AAAARecordData, MXRecordData, TXTRecordData,
                CAARecordData, CNAMERecordData, NAPTRRecordData, NSRecordData,
                PTRRecordData, SOARecordData, SRVRecordData]

@dataclass
class DNSResult:
    """Represents a complete DNS query result with all sections"""
    answer: list[DNSRecord]
    authority: list[DNSRecord]
    additional: list[DNSRecord]


# Base class for legacy compatibility (if needed)
class AresResult:
    __slots__ = ()

    def __repr__(self):
        attrs = ['%s=%s' % (a, getattr(self, a)) for a in self.__slots__]
        return '<%s> %s' % (self.__class__.__name__, ', '.join(attrs))


# Other result types
#

class ares_host_result(AresResult):
    __slots__ = ('name', 'aliases', 'addresses')

    def __init__(self, hostent):
        self.name = maybe_str(_ffi.string(hostent.h_name))
        self.aliases = []
        self.addresses = []
        i = 0
        while hostent.h_aliases[i] != _ffi.NULL:
            self.aliases.append(maybe_str(_ffi.string(hostent.h_aliases[i])))
            i += 1

        i = 0
        while hostent.h_addr_list[i] != _ffi.NULL:
            buf = _ffi.new("char[]", _lib.INET6_ADDRSTRLEN)
            if _ffi.NULL != _lib.ares_inet_ntop(hostent.h_addrtype, hostent.h_addr_list[i], buf, _lib.INET6_ADDRSTRLEN):
                self.addresses.append(maybe_str(_ffi.string(buf, _lib.INET6_ADDRSTRLEN)))
            i += 1


class ares_nameinfo_result(AresResult):
    __slots__ = ('node', 'service')

    def __init__(self, node, service):
        self.node = maybe_str(_ffi.string(node))
        self.service = maybe_str(_ffi.string(service)) if service != _ffi.NULL else None


class ares_addrinfo_node_result(AresResult):
    __slots__ = ('ttl', 'flags', 'family', 'socktype', 'protocol', 'addr')

    def __init__(self, ares_node):
        self.ttl = ares_node.ai_ttl
        self.flags = ares_node.ai_flags
        self.socktype = ares_node.ai_socktype
        self.protocol = ares_node.ai_protocol

        addr = ares_node.ai_addr
        assert addr.sa_family == ares_node.ai_family
        ip = _ffi.new("char []", _lib.INET6_ADDRSTRLEN)
        if addr.sa_family == socket.AF_INET:
            self.family = socket.AF_INET
            s = _ffi.cast("struct sockaddr_in*", addr)
            if _ffi.NULL != _lib.ares_inet_ntop(s.sin_family, _ffi.addressof(s.sin_addr), ip, _lib.INET6_ADDRSTRLEN):
                # (address, port) 2-tuple for AF_INET
                self.addr = (_ffi.string(ip, _lib.INET6_ADDRSTRLEN), socket.ntohs(s.sin_port))
        elif addr.sa_family == socket.AF_INET6:
            self.family = socket.AF_INET6
            s = _ffi.cast("struct sockaddr_in6*", addr)
            if _ffi.NULL != _lib.ares_inet_ntop(s.sin6_family, _ffi.addressof(s.sin6_addr), ip, _lib.INET6_ADDRSTRLEN):
                # (address, port, flow info, scope id) 4-tuple for AF_INET6
                self.addr = (_ffi.string(ip, _lib.INET6_ADDRSTRLEN), socket.ntohs(s.sin6_port), s.sin6_flowinfo, s.sin6_scope_id)
        else:
            raise ValueError("invalid sockaddr family")


class ares_addrinfo_cname_result(AresResult):
    __slots__ = ('ttl', 'alias', 'name')

    def __init__(self, ares_cname):
        self.ttl = ares_cname.ttl
        self.alias = maybe_str(_ffi.string(ares_cname.alias))
        self.name = maybe_str(_ffi.string(ares_cname.name))


class ares_addrinfo_result(AresResult):
    __slots__ = ('cnames', 'nodes')

    def __init__(self, ares_addrinfo):
        self.cnames = []
        self.nodes = []
        cname_ptr = ares_addrinfo.cnames
        while cname_ptr != _ffi.NULL:
            self.cnames.append(ares_addrinfo_cname_result(cname_ptr))
            cname_ptr = cname_ptr.next
        node_ptr = ares_addrinfo.nodes
        while node_ptr != _ffi.NULL:
            self.nodes.append(ares_addrinfo_node_result(node_ptr))
            node_ptr = node_ptr.ai_next
        _lib.ares_freeaddrinfo(ares_addrinfo)


def ares_threadsafety() -> bool:
    """
    Check if c-ares was compiled with thread safety support.

    :return: True if thread-safe, False otherwise.
    :rtype: bool
    """
    return bool(_lib.ares_threadsafety())

__all__ = (
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
    "QUERY_TYPE_MX",
    "QUERY_TYPE_NAPTR",
    "QUERY_TYPE_NS",
    "QUERY_TYPE_PTR",
    "QUERY_TYPE_SOA",
    "QUERY_TYPE_SRV",
    "QUERY_TYPE_TXT",

    # Query classes
    "QUERY_CLASS_IN",
    "QUERY_CLASS_CHAOS",
    "QUERY_CLASS_HS",
    "QUERY_CLASS_NONE",
    "QUERY_CLASS_ANY",


    "ARES_VERSION",
    "AresError",
    "Channel",
    "ares_threadsafety",
    "errno",
    "__version__",

    # New DNS record result types
    "DNSResult",
    "DNSRecord",
    "ARecordData",
    "AAAARecordData",
    "MXRecordData",
    "TXTRecordData",
    "CAARecordData",
    "CNAMERecordData",
    "NAPTRRecordData",
    "NSRecordData",
    "PTRRecordData",
    "SOARecordData",
    "SRVRecordData",
)
