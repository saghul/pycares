from ._cares import ffi as _ffi, lib as _lib
import _cffi_backend  # hint for bundler tools


if _lib.ARES_SUCCESS != _lib.ares_library_init(_lib.ARES_LIB_INIT_ALL) or _ffi is None:
    raise RuntimeError("Could not initialize c-ares")

from . import errno
from .utils import ascii_bytes, maybe_str, parse_name
from ._version import __version__

import math
import socket
import threading
from collections.abc import Callable, Iterable
from typing import Any, Callable, Final, Optional, Dict, Union, Literal, overload
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
ARES_SOCKET_BAD: int = _lib.ARES_SOCKET_BAD

# Query types
QUERY_TYPE_A: Literal[1] = _lib.T_A
QUERY_TYPE_AAAA: Literal[28] = _lib.T_AAAA
QUERY_TYPE_ANY: Literal[255] = _lib.T_ANY
QUERY_TYPE_CAA: Literal[257] = _lib.T_CAA
QUERY_TYPE_CNAME: Literal[5] = _lib.T_CNAME
QUERY_TYPE_MX: Literal[15] = _lib.T_MX
QUERY_TYPE_NAPTR: Literal[35] = _lib.T_NAPTR
QUERY_TYPE_NS: Literal[2] = _lib.T_NS
QUERY_TYPE_PTR: Literal[12] = _lib.T_PTR
QUERY_TYPE_SOA: Literal[6] = _lib.T_SOA
QUERY_TYPE_SRV: Literal[33] = _lib.T_SRV
QUERY_TYPE_TXT: Literal[16] = _lib.T_TXT

# Query classes
QUERY_CLASS_IN: int = _lib.C_IN
QUERY_CLASS_CHAOS: int = _lib.C_CHAOS
QUERY_CLASS_HS: int = _lib.C_HS
QUERY_CLASS_NONE: int = _lib.C_NONE
QUERY_CLASS_ANY: int = _lib.C_ANY

ARES_VERSION = maybe_str(_ffi.string(_lib.ares_version(_ffi.NULL)))
PYCARES_ADDRTTL_SIZE = 256


class AresError(Exception):
    pass


# callback helpers

_handle_to_channel: Dict[
    Any, "Channel"
] = {}  # Maps handle to channel to prevent use-after-free


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
def _query_cb(arg, status, timeouts, abuf, alen):
    # Get callback data without removing the reference yet
    if arg not in _handle_to_channel:
        return

    callback, query_type = _ffi.from_handle(arg)

    if status == _lib.ARES_SUCCESS:
        if query_type == _lib.T_ANY:
            result = []
            for qtype in (
                _lib.T_A,
                _lib.T_AAAA,
                _lib.T_CAA,
                _lib.T_CNAME,
                _lib.T_MX,
                _lib.T_NAPTR,
                _lib.T_NS,
                _lib.T_PTR,
                _lib.T_SOA,
                _lib.T_SRV,
                _lib.T_TXT,
            ):
                r, status = parse_result(qtype, abuf, alen)
                if status not in (None, _lib.ARES_ENODATA, _lib.ARES_EBADRESP):
                    result = None
                    break
                if r is not None:
                    if isinstance(r, Iterable):
                        result.extend(r)
                    else:
                        result.append(r)
            else:
                status = None
        else:
            result, status = parse_result(query_type, abuf, alen)
    else:
        result = None

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


def parse_result(query_type, abuf, alen):
    if query_type == _lib.T_A:
        addrttls = _ffi.new("struct ares_addrttl[]", PYCARES_ADDRTTL_SIZE)
        naddrttls = _ffi.new("int*", PYCARES_ADDRTTL_SIZE)
        parse_status = _lib.ares_parse_a_reply(
            abuf, alen, _ffi.NULL, addrttls, naddrttls
        )
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = [ares_query_a_result(addrttls[i]) for i in range(naddrttls[0])]
            status = None
    elif query_type == _lib.T_AAAA:
        addrttls = _ffi.new("struct ares_addr6ttl[]", PYCARES_ADDRTTL_SIZE)
        naddrttls = _ffi.new("int*", PYCARES_ADDRTTL_SIZE)
        parse_status = _lib.ares_parse_aaaa_reply(
            abuf, alen, _ffi.NULL, addrttls, naddrttls
        )
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = [ares_query_aaaa_result(addrttls[i]) for i in range(naddrttls[0])]
            status = None
    elif query_type == _lib.T_CAA:
        caa_reply = _ffi.new("struct ares_caa_reply **")
        parse_status = _lib.ares_parse_caa_reply(abuf, alen, caa_reply)
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = []
            caa_reply_ptr = caa_reply[0]
            while caa_reply_ptr != _ffi.NULL:
                result.append(ares_query_caa_result(caa_reply_ptr))
                caa_reply_ptr = caa_reply_ptr.next
            _lib.ares_free_data(caa_reply[0])
            status = None
    elif query_type == _lib.T_CNAME:
        host = _ffi.new("struct hostent **")
        parse_status = _lib.ares_parse_a_reply(abuf, alen, host, _ffi.NULL, _ffi.NULL)
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = ares_query_cname_result(host[0])
            _lib.ares_free_hostent(host[0])
            status = None
    elif query_type == _lib.T_MX:
        mx_reply = _ffi.new("struct ares_mx_reply **")
        parse_status = _lib.ares_parse_mx_reply(abuf, alen, mx_reply)
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = []
            mx_reply_ptr = mx_reply[0]
            while mx_reply_ptr != _ffi.NULL:
                result.append(ares_query_mx_result(mx_reply_ptr))
                mx_reply_ptr = mx_reply_ptr.next
            _lib.ares_free_data(mx_reply[0])
            status = None
    elif query_type == _lib.T_NAPTR:
        naptr_reply = _ffi.new("struct ares_naptr_reply **")
        parse_status = _lib.ares_parse_naptr_reply(abuf, alen, naptr_reply)
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = []
            naptr_reply_ptr = naptr_reply[0]
            while naptr_reply_ptr != _ffi.NULL:
                result.append(ares_query_naptr_result(naptr_reply_ptr))
                naptr_reply_ptr = naptr_reply_ptr.next
            _lib.ares_free_data(naptr_reply[0])
            status = None
    elif query_type == _lib.T_NS:
        hostent = _ffi.new("struct hostent **")
        parse_status = _lib.ares_parse_ns_reply(abuf, alen, hostent)
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = []
            host = hostent[0]
            i = 0
            while host.h_aliases[i] != _ffi.NULL:
                result.append(ares_query_ns_result(host.h_aliases[i]))
                i += 1
            _lib.ares_free_hostent(host)
            status = None
    elif query_type == _lib.T_PTR:
        hostent = _ffi.new("struct hostent **")
        parse_status = _lib.ares_parse_ptr_reply(
            abuf, alen, _ffi.NULL, 0, socket.AF_UNSPEC, hostent
        )
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            aliases = []
            host = hostent[0]
            i = 0
            while host.h_aliases[i] != _ffi.NULL:
                aliases.append(maybe_str(_ffi.string(host.h_aliases[i])))
                i += 1
            result = ares_query_ptr_result(host, aliases)
            _lib.ares_free_hostent(host)
            status = None
    elif query_type == _lib.T_SOA:
        soa_reply = _ffi.new("struct ares_soa_reply **")
        parse_status = _lib.ares_parse_soa_reply(abuf, alen, soa_reply)
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = ares_query_soa_result(soa_reply[0])
            _lib.ares_free_data(soa_reply[0])
            status = None
    elif query_type == _lib.T_SRV:
        srv_reply = _ffi.new("struct ares_srv_reply **")
        parse_status = _lib.ares_parse_srv_reply(abuf, alen, srv_reply)
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = []
            srv_reply_ptr = srv_reply[0]
            while srv_reply_ptr != _ffi.NULL:
                result.append(ares_query_srv_result(srv_reply_ptr))
                srv_reply_ptr = srv_reply_ptr.next
            _lib.ares_free_data(srv_reply[0])
            status = None
    elif query_type == _lib.T_TXT:
        txt_reply = _ffi.new("struct ares_txt_ext **")
        parse_status = _lib.ares_parse_txt_reply_ext(abuf, alen, txt_reply)
        if parse_status != _lib.ARES_SUCCESS:
            result = None
            status = parse_status
        else:
            result = []
            txt_reply_ptr = txt_reply[0]
            tmp_obj = None
            while True:
                if txt_reply_ptr == _ffi.NULL:
                    if tmp_obj is not None:
                        result.append(ares_query_txt_result(tmp_obj))
                    break
                if txt_reply_ptr.record_start == 1:
                    if tmp_obj is not None:
                        result.append(ares_query_txt_result(tmp_obj))
                    tmp_obj = ares_query_txt_result_chunk(txt_reply_ptr)
                else:
                    new_chunk = ares_query_txt_result_chunk(txt_reply_ptr)
                    tmp_obj.text += new_chunk.text
                txt_reply_ptr = txt_reply_ptr.next
            _lib.ares_free_data(txt_reply[0])
            status = None
    else:
        raise ValueError("invalid query type specified")

    return result, status


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
            self._thread = threading.Thread(
                target=self._run_safe_shutdown_loop, daemon=True
            )
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
    """
    The c-ares ``Channel`` provides asynchronous DNS operations.

    The Channel object is designed to handle an unlimited number of DNS queries efficiently.
    Creating and destroying resolver instances repeatedly is resource-intensive and not
    recommended. Instead, create a single resolver instance and reuse it throughout your
    application's lifetime.
    """

    __qtypes__ = (
        _lib.T_A,
        _lib.T_AAAA,
        _lib.T_ANY,
        _lib.T_CAA,
        _lib.T_CNAME,
        _lib.T_MX,
        _lib.T_NAPTR,
        _lib.T_NS,
        _lib.T_PTR,
        _lib.T_SOA,
        _lib.T_SRV,
        _lib.T_TXT,
    )
    __qclasses__ = (_lib.C_IN, _lib.C_CHAOS, _lib.C_HS, _lib.C_NONE, _lib.C_ANY)

    def __init__(
        self,
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
        event_thread: bool = False,
    ) -> None:
        """
        Args:
            flags: Flags controlling the behavior of the resolver.
                See ``constants`` for available values.

            timeout: The number of seconds each name server is given to respond to
                a query on the first try. The default is five seconds.

            tries: The number of tries the resolver will try contacting each name 
                server before giving up. The default is four tries. 

            ndots: The number of dots which must be present in a domain name for it
                to be queried for "as is" prior to querying for it with the default domain
                extensions appended. The default value is 1 unless set otherwise by resolv.conf
                or the RES_OPTIONS environment variable.

            tcp_port: The (TCP) port to use for queries. The default is 53.

            udp_port: The (UDP) port to use for queries. The default is 53.

            servers: List of nameservers to be used to do the lookups.

            domains: The domains to search, instead of the domains specified
                in resolv.conf or the domain derived from the kernel hostname variable.

            lookups: The lookups to perform for host queries. lookups should
                be set to a string of the characters "b" or "f", where "b" indicates a \
                DNS lookup and "f" indicates a lookup in the hosts file.

            sock_state_cb: A callback function to be invoked when a
                socket changes state. Callback signature: ``sock_state_cb(self, fd, readable, writable)``

                This option is mutually exclusive with the ``event_thread`` option.

            event_thread: If set to True, c-ares will use its own thread
                to process events. This is the recommended way to use c-ares, as it
                allows for automatic reinitialization of the channel when the
                system resolver configuration changes. Verify that c-ares was
                compiled with thread-safety by calling `ares_threadsafety`
                before using this option. This option is mutually exclusive with the
                ``sock_state_cb`` option.

            socket_send_buffer_size: Size for the created socket's send buffer.

            socket_receive_buffer_size: Size for the created socket's receive buffer.

            rotate: If set to True, the nameservers are rotated when doing queries.

            local_ip: Sets the local IP address for DNS operations.

            local_dev: Sets the local network adapter to use for DNS operations. Linux only.

            resolvconf_path: Path to resolv.conf, defaults to /etc/resolv.conf. Unix only.
        """

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
            optmask = optmask | _lib.ARES_OPT_TRIES

        if ndots is not None:
            options.ndots = ndots
            optmask = optmask | _lib.ARES_OPT_NDOTS

        if tcp_port is not None:
            options.tcp_port = tcp_port
            optmask = optmask | _lib.ARES_OPT_TCP_PORT

        if udp_port is not None:
            options.udp_port = udp_port
            optmask = optmask | _lib.ARES_OPT_UDP_PORT

        if socket_send_buffer_size is not None:
            options.socket_send_buffer_size = socket_send_buffer_size
            optmask = optmask | _lib.ARES_OPT_SOCK_SNDBUF

        if socket_receive_buffer_size is not None:
            options.socket_receive_buffer_size = socket_receive_buffer_size
            optmask = optmask | _lib.ARES_OPT_SOCK_RCVBUF

        if sock_state_cb:
            if not callable(sock_state_cb):
                raise TypeError("sock_state_cb is not callable")
            if event_thread:
                raise RuntimeError(
                    "sock_state_cb and event_thread cannot be used together"
                )

            userdata = _ffi.new_handle(sock_state_cb)

            # This must be kept alive while the channel is alive.
            self._sock_state_cb_handle = userdata

            options.sock_state_cb = _lib._sock_state_cb
            options.sock_state_cb_data = userdata
            optmask = optmask | _lib.ARES_OPT_SOCK_STATE_CB

        if event_thread:
            if not ares_threadsafety():
                raise RuntimeError("c-ares is not built with thread safety")
            if sock_state_cb:
                raise RuntimeError(
                    "sock_state_cb and event_thread cannot be used together"
                )
            optmask = optmask | _lib.ARES_OPT_EVENT_THREAD
            options.evsys = _lib.ARES_EVSYS_DEFAULT

        if lookups:
            options.lookups = _ffi.new("char[]", ascii_bytes(lookups))
            optmask = optmask | _lib.ARES_OPT_LOOKUPS

        if domains:
            strs = [_ffi.new("char[]", ascii_bytes(i)) for i in domains]
            c = _ffi.new("char *[%d]" % (len(domains) + 1))
            for i in range(len(domains)):
                c[i] = strs[i]

            options.domains = c
            options.ndomains = len(domains)
            optmask = optmask | _lib.ARES_OPT_DOMAINS

        if rotate:
            optmask = optmask | _lib.ARES_OPT_ROTATE

        if resolvconf_path is not None:
            optmask = optmask | _lib.ARES_OPT_RESOLVCONF
            options.resolvconf_path = _ffi.new("char[]", ascii_bytes(resolvconf_path))

        r = _lib.ares_init_options(channel, options, optmask)
        if r != _lib.ARES_SUCCESS:
            raise AresError("Failed to initialize c-ares channel")

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

    def _create_callback_handle(
        self, callback_data: Union[Callable[..., None], tuple[Any, ...]]
    ):
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
        """Cancel any pending query on this channel. All pending callbacks will be called with ARES_ECANCELLED errorno."""
        _lib.ares_cancel(self._channel[0])

    def reinit(self) -> None:
        """
        Reinitialize the channel.

        For more details, see the `ares_reinit documentation <https://c-ares.org/docs/ares_reinit.html>`_.

        Raises:
            AresError: If ``ares_reinit`` was unsuccessful
        """
        r = _lib.ares_reinit(self._channel[0])
        if r != _lib.ARES_SUCCESS:
            raise AresError(r, errno.strerror(r))

    @property
    def servers(self) -> list[str]:
        """
        Obtains a list of current servers being used by this channel
        Raises:
            AresError: if C function `ares_get_servers <https://c-ares.org/docs/ares_reinit.html>`_
                was unsuccessful

            ValueError: When Setting new servers for this property if an
                invalid IPV4 or IPV6 Address was given
        """
        servers = _ffi.new("struct ares_addr_node **")

        r = _lib.ares_get_servers(self._channel[0], servers)
        if r != _lib.ARES_SUCCESS:
            raise AresError(r, errno.strerror(r))

        server_list = []
        server = _ffi.new("struct ares_addr_node **", servers[0])
        while True:
            if server == _ffi.NULL:
                break

            ip = _ffi.new("char []", _lib.INET6_ADDRSTRLEN)
            s = server[0]
            if _ffi.NULL != _lib.ares_inet_ntop(
                s.family, _ffi.addressof(s.addr), ip, _lib.INET6_ADDRSTRLEN
            ):
                server_list.append(maybe_str(_ffi.string(ip, _lib.INET6_ADDRSTRLEN)))

            server = s.next

        return server_list

    @servers.setter
    def servers(self, servers: Iterable[Union[str, bytes]]) -> None:
        c = _ffi.new("struct ares_addr_node[%d]" % len(servers))
        for i, server in enumerate(servers):
            if (
                _lib.ares_inet_pton(
                    socket.AF_INET, ascii_bytes(server), _ffi.addressof(c[i].addr.addr4)
                )
                == 1
            ):
                c[i].family = socket.AF_INET
            elif (
                _lib.ares_inet_pton(
                    socket.AF_INET6,
                    ascii_bytes(server),
                    _ffi.addressof(c[i].addr.addr6),
                )
                == 1
            ):
                c[i].family = socket.AF_INET6
            else:
                raise ValueError("invalid IP address")

            if i > 0:
                c[i - 1].next = _ffi.addressof(c[i])

        r = _lib.ares_set_servers(self._channel[0], c)
        if r != _lib.ARES_SUCCESS:
            raise AresError(r, errno.strerror(r))

    def getsock(self) -> tuple[list[int], list[int]]:
        """
        Return a tuple containing 2 lists with the file descriptors
        ready to read and write.
        """
        rfds = []
        wfds = []
        socks = _ffi.new("ares_socket_t [%d]" % _lib.ARES_GETSOCK_MAXNUM)
        bitmask = _lib.ares_getsock(self._channel[0], socks, _lib.ARES_GETSOCK_MAXNUM)
        for i in range(_lib.ARES_GETSOCK_MAXNUM):
            if _lib.ARES_GETSOCK_READABLE(bitmask, i):
                rfds.append(socks[i])
            if _lib.ARES_GETSOCK_WRITABLE(bitmask, i):
                wfds.append(socks[i])

        return rfds, wfds

    def process_fd(self, read_fd: int, write_fd: int) -> None:
        """Process the given file descriptors for read and/or write events.
        Args:
            read_fd: File descriptor ready to read from.

            write_fd: File descriptor ready to write to.
        """
        _lib.ares_process_fd(
            self._channel[0],
            _ffi.cast("ares_socket_t", read_fd),
            _ffi.cast("ares_socket_t", write_fd),
        )

    def process_read_fd(self, read_fd: int) -> None:
        """Processes the given file file descriptors for read events
        Args:
            read_fd: File descriptor ready to read from.
        """
        _lib.ares_process_fd(
            self._channel[0],
            _ffi.cast("ares_socket_t", read_fd),
            _ffi.cast("ares_socket_t", ARES_SOCKET_BAD),
        )

    def process_write_fd(self, write_fd: int) -> None:
        """Processes the given file file descriptors for write events
        Args:
            write_fd: File descriptor ready to write to.
        """
        _lib.ares_process_fd(
            self._channel[0],
            _ffi.cast("ares_socket_t", ARES_SOCKET_BAD),
            _ffi.cast("ares_socket_t", write_fd),
        )

    def timeout(self, max_timeout: Optional[float] = None) -> float:
        """
        Determines the maximum time for which the caller should wait before invoking ``process_fd`` to process timeouts.
        If the ``max_timeout`` parameter is specified, it is stored on the channel and the appropriate value is then
        returned.

        Args:
            max_timeout: Maximum timeout.
        """
        maxtv = _ffi.NULL
        tv = _ffi.new("struct timeval*")

        if max_timeout is not None:
            if max_timeout >= 0.0:
                maxtv = _ffi.new("struct timeval*")
                maxtv.tv_sec = int(math.floor(max_timeout))
                maxtv.tv_usec = int(math.fmod(max_timeout, 1.0) * 1000000)
            else:
                raise ValueError("timeout needs to be a positive number or None")

        _lib.ares_timeout(self._channel[0], maxtv, tv)

        if tv == _ffi.NULL:
            return 0.0

        return tv.tv_sec + tv.tv_usec / 1000000.0

    def gethostbyaddr(
        self,
        addr: str,
        callback: Callable[[Optional["ares_nameinfo_result"], int], None],
    ) -> None:
        """
        Retrieves the host information corresponding to a network address.

        Args:
            name: Name to query.

            callback: Callback to be called with the result of the query.
                Retrieves the host information corresponding to a network address.
                Callback signature: ``callback(result, errorno)``

         Raises:
            TypeError: if callback is not callable or IP address is invalid
        """

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
        _lib.ares_gethostbyaddr(
            self._channel[0],
            address,
            _ffi.sizeof(address[0]),
            family,
            _lib._host_cb,
            userdata,
        )

    def gethostbyname(
        self,
        name: str,
        family: socket.AddressFamily,
        callback: Callable[[Optional["ares_nameinfo_result"], int], None],
    ) -> None:
        """
        Retrieves host information corresponding to a host name from a host database.
        Callback signature: ``callback(result, errorno)``

        Args:
            name: Name to query.

            family: Socket family.

            callback: Callback to be called with the result of the query.

        Raises:
            TypeError: if callback is not callable
        """

        if not callable(callback):
            raise TypeError("a callable is required")

        userdata = self._create_callback_handle(callback)
        _lib.ares_gethostbyname(
            self._channel[0], parse_name(name), family, _lib._host_cb, userdata
        )

    def getaddrinfo(
        self,
        host: str,
        port: Optional[int],
        callback: Callable[[Optional["ares_addrinfo_result"], int], None],
        family: Union[socket.AddressFamily, Literal[0]] = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> None:
        """
        The ``family``, ``type`` and ``proto`` arguments can be optionally specified in order to narrow the list of
        addresses returned. Passing zero as a value for each of these arguments selects the full range of results.
        The ``flags`` argument can be one or several of the ``AI_*`` constants, and will influence how results are
        computed and returned. For example, ``AI_NUMERICHOST`` will disable domain name resolution.

        Translate the host/port argument into a sequence of 5-tuples that contain all the necessary arguments for
        creating a socket connected to that service.

        Callback signature: ``callback(result, errorno)``

        Args:
            address: address tuple to get info about.

            flags: Query flags, see the NI flags section.

            callback: Callback to be called with the result of the query.

        Raises:
            TypeError: if callable is not callable

        """

        if not callable(callback):
            raise TypeError("a callable is required")

        if port is None:
            service = _ffi.NULL
        elif isinstance(port, int):
            service = str(port).encode("ascii")
        else:
            service = ascii_bytes(port)

        userdata = self._create_callback_handle(callback)

        hints = _ffi.new("struct ares_addrinfo_hints*")
        hints.ai_flags = flags
        hints.ai_family = family
        hints.ai_socktype = type
        hints.ai_protocol = proto
        _lib.ares_getaddrinfo(
            self._channel[0],
            parse_name(host),
            service,
            hints,
            _lib._addrinfo_cb,
            userdata,
        )

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[1],
        callback: Callable[[list["ares_query_a_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[28],
        callback: Callable[[list["ares_query_aaaa_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[255],
        callback: Callable[["AresResult", int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[257],
        callback: Callable[[list["ares_query_caa_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[5],
        callback: Callable[["ares_query_cname_result", int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[15],
        callback: Callable[[list["ares_query_mx_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[35],
        callback: Callable[[list["ares_query_naptr_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[2],
        callback: Callable[[list["ares_query_ns_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[12],
        callback: Callable[[list["ares_query_ptr_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[6],
        callback: Callable[["ares_query_soa_result", int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[33],
        callback: Callable[[list["ares_query_srv_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def query(
        self,
        name: Union[str, bytes],
        query_type: Literal[16],
        callback: Callable[[list["ares_query_txt_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    def query(
        self,
        name: Union[str, bytes],
        query_type: int,
        callback: Callable[["AresResult", int], None],
        query_class: Optional[int] = None,
    ) -> None:
        """
        Do a DNS query of the specified type.

        Available types:
            - ``QUERY_TYPE_A``
            - ``QUERY_TYPE_AAAA``
            - ``QUERY_TYPE_ANY``
            - ``QUERY_TYPE_CAA``
            - ``QUERY_TYPE_CNAME``
            - ``QUERY_TYPE_MX``
            - ``QUERY_TYPE_NAPTR``
            - ``QUERY_TYPE_NS``
            - ``QUERY_TYPE_PTR``
            - ``QUERY_TYPE_SOA``
            - ``QUERY_TYPE_SRV``
            - ``QUERY_TYPE_TXT``

        Args:
            name: Name to query.

            query_type: Type of query to perform.

            callback: Callback to be called with the result of the query.


        Raises:
            TypeError: if callaback is not callable

            ValueError: if invalid query type or class was specified

        """
        self._do_query(
            _lib.ares_query, name, query_type, callback, query_class=query_class
        )

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[1],
        callback: Callable[[list["ares_query_a_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[28],
        callback: Callable[[list["ares_query_aaaa_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[255],
        callback: Callable[["AresResult", int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[257],
        callback: Callable[[list["ares_query_caa_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[5],
        callback: Callable[["ares_query_cname_result", int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[15],
        callback: Callable[[list["ares_query_mx_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[35],
        callback: Callable[[list["ares_query_naptr_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[2],
        callback: Callable[[list["ares_query_ns_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[12],
        callback: Callable[[list["ares_query_ptr_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[6],
        callback: Callable[["ares_query_soa_result", int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[33],
        callback: Callable[[list["ares_query_srv_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    @overload
    def search(
        self,
        name: Union[str, bytes],
        query_type: Literal[16],
        callback: Callable[[list["ares_query_txt_result"], int], None],
        query_class: Optional[int] = ...,
    ) -> None: ...

    def search(
        self,
        name: Union[str, bytes],
        query_type: int,
        callback: Callable[["AresResult", int], None],
        query_class: Optional[int] = None,
    ):
        """
        This function does the same as `query` but it will honor the ``domain`` and ``search`` directives in ``resolv.conf``.
        Args:
            name: Name to query.

            query_type: Type of query to perform.

            callback: Callback to be called with the result of the query.

        Raises:
            TypeError: if callaback is not callable

            ValueError: if invalid query type or class was specified
        """
        self._do_query(
            _lib.ares_search, name, query_type, callback, query_class=query_class
        )

    def _do_query(
        self,
        func: Any,
        name: Union[str, bytes],
        query_type: int,
        callback: Callable[[Optional["ares_addrinfo_result"], int], None],
        query_class: Optional[Union[str, int]] = None,
    ):
        if not callable(callback):
            raise TypeError("a callable is required")

        if query_type not in self.__qtypes__:
            raise ValueError("invalid query type specified")

        if query_class is None:
            query_class = _lib.C_IN

        if query_class not in self.__qclasses__:
            raise ValueError("invalid query class specified")

        userdata = self._create_callback_handle((callback, query_type))
        func(
            self._channel[0],
            parse_name(name),
            query_class,
            query_type,
            _lib._query_cb,
            userdata,
        )

    def set_local_ip(self, ip: Union[str, bytes]) -> None:
        """Set the local IPv4 or IPv6 address from which the queries will be sent.
        Args:
            ip: IP Address.
        """
        addr4 = _ffi.new("struct in_addr*")
        addr6 = _ffi.new("struct ares_in6_addr*")
        if _lib.ares_inet_pton(socket.AF_INET, ascii_bytes(ip), addr4) == 1:
            _lib.ares_set_local_ip4(self._channel[0], socket.ntohl(addr4.s_addr))
        elif _lib.ares_inet_pton(socket.AF_INET6, ascii_bytes(ip), addr6) == 1:
            _lib.ares_set_local_ip6(self._channel[0], addr6)
        else:
            raise ValueError("invalid IP address")

    def getnameinfo(
        self,
        address: Union[IP4, IP6],
        flags: int,
        callback: Callable[["ares_nameinfo_result", int], None],
    ) -> None:
        """
        Provides protocol-independent name resolution from an address to a host name and
        from a port number to the service name.

        ``address`` must be a 2-item tuple for IPv4 or a 4-item tuple for IPv6. Format of
        fields is the same as one returned by `getaddrinfo()`.

        Callback signature: ``callback(result, errorno)``

        Args:
            address: address tuple to get info about.

            flags: Query flags, see the NI flags section.

            callback: Callback to be called with the result of the query.

        Raises:
            TypeError: if callback is not callable or address or address's host field is invalid
        """

        if not callable(callback):
            raise TypeError("a callable is required")

        if len(address) == 2:
            (ip, port) = address
            sa4 = _ffi.new("struct sockaddr_in*")
            if (
                _lib.ares_inet_pton(
                    socket.AF_INET, ascii_bytes(ip), _ffi.addressof(sa4.sin_addr)
                )
                != 1
            ):
                raise ValueError("Invalid IPv4 address %r" % ip)
            sa4.sin_family = socket.AF_INET
            sa4.sin_port = socket.htons(port)
            sa = sa4
        elif len(address) == 4:
            (ip, port, flowinfo, scope_id) = address
            sa6 = _ffi.new("struct sockaddr_in6*")
            if (
                _lib.ares_inet_pton(
                    socket.AF_INET6, ascii_bytes(ip), _ffi.addressof(sa6.sin6_addr)
                )
                != 1
            ):
                raise ValueError("Invalid IPv6 address %r" % ip)
            sa6.sin6_family = socket.AF_INET6
            sa6.sin6_port = socket.htons(port)
            sa6.sin6_flowinfo = socket.htonl(
                flowinfo
            )  # I'm unsure about byteorder here.
            sa6.sin6_scope_id = scope_id  # Yes, without htonl.
            sa = sa6
        else:
            raise ValueError("Invalid address argument")

        userdata = self._create_callback_handle(callback)
        _lib.ares_getnameinfo(
            self._channel[0],
            _ffi.cast("struct sockaddr*", sa),
            _ffi.sizeof(sa[0]),
            flags,
            _lib._nameinfo_cb,
            userdata,
        )

    def set_local_dev(self, dev: str):
        """
        Set the local ethernet device from which the queries will be sent.
        Args:
            dev: Network device name.
        """
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


class AresResult:
    __slots__ = ()

    def __repr__(self):
        attrs = ["%s=%s" % (a, getattr(self, a)) for a in self.__slots__]
        return "<%s> %s" % (self.__class__.__name__, ", ".join(attrs))


# DNS query result types
#


class ares_query_a_result(AresResult):
    __slots__ = ("host", "ttl")
    type: Final = "A"

    def __init__(self, ares_addrttl):
        buf = _ffi.new("char[]", _lib.INET6_ADDRSTRLEN)
        _lib.ares_inet_ntop(
            socket.AF_INET,
            _ffi.addressof(ares_addrttl.ipaddr),
            buf,
            _lib.INET6_ADDRSTRLEN,
        )
        self.host = maybe_str(_ffi.string(buf, _lib.INET6_ADDRSTRLEN))
        self.ttl = ares_addrttl.ttl


class ares_query_aaaa_result(AresResult):
    __slots__ = ("host", "ttl")
    type: Final = "AAAA"

    def __init__(self, ares_addrttl):
        buf = _ffi.new("char[]", _lib.INET6_ADDRSTRLEN)
        _lib.ares_inet_ntop(
            socket.AF_INET6,
            _ffi.addressof(ares_addrttl.ip6addr),
            buf,
            _lib.INET6_ADDRSTRLEN,
        )
        self.host = maybe_str(_ffi.string(buf, _lib.INET6_ADDRSTRLEN))
        self.ttl = ares_addrttl.ttl


class ares_query_caa_result(AresResult):
    __slots__ = ("critical", "property", "value", "ttl")
    type: Final = "CAA"

    def __init__(self, caa):
        self.critical = caa.critical
        self.property = maybe_str(_ffi.string(caa.property, caa.plength))
        self.value = maybe_str(_ffi.string(caa.value, caa.length))
        self.ttl = -1


class ares_query_cname_result(AresResult):
    __slots__ = ("cname", "ttl")
    type: Final = "CNAME"

    def __init__(self, host):
        self.cname = maybe_str(_ffi.string(host.h_name))
        self.ttl = -1


class ares_query_mx_result(AresResult):
    __slots__ = ("host", "priority", "ttl")
    type: Final = "MX"

    def __init__(self, mx):
        self.host = maybe_str(_ffi.string(mx.host))
        self.priority = mx.priority
        self.ttl = -1


class ares_query_naptr_result(AresResult):
    __slots__ = (
        "order",
        "preference",
        "flags",
        "service",
        "regex",
        "replacement",
        "ttl",
    )
    type: Final = "NAPTR"

    def __init__(self, naptr):
        self.order = naptr.order
        self.preference = naptr.preference
        self.flags = maybe_str(_ffi.string(naptr.flags))
        self.service = maybe_str(_ffi.string(naptr.service))
        self.regex = maybe_str(_ffi.string(naptr.regexp))
        self.replacement = maybe_str(_ffi.string(naptr.replacement))
        self.ttl = -1


class ares_query_ns_result(AresResult):
    __slots__ = ("host", "ttl")
    type: Final = "NS"

    def __init__(self, ns):
        self.host = maybe_str(_ffi.string(ns))
        self.ttl = -1


class ares_query_ptr_result(AresResult):
    __slots__ = ("name", "ttl", "aliases")
    type: Final = "PTR"

    def __init__(self, hostent, aliases):
        self.name = maybe_str(_ffi.string(hostent.h_name))
        self.aliases = aliases
        self.ttl = -1


class ares_query_soa_result(AresResult):
    __slots__ = (
        "nsname",
        "hostmaster",
        "serial",
        "refresh",
        "retry",
        "expires",
        "minttl",
        "ttl",
    )
    type: Final = "SOA"

    def __init__(self, soa):
        self.nsname = maybe_str(_ffi.string(soa.nsname))
        self.hostmaster = maybe_str(_ffi.string(soa.hostmaster))
        self.serial = soa.serial
        self.refresh = soa.refresh
        self.retry = soa.retry
        self.expires = soa.expire
        self.minttl = soa.minttl
        self.ttl = -1


class ares_query_srv_result(AresResult):
    __slots__ = ("host", "port", "priority", "weight", "ttl")
    type: Final = "SRV"

    def __init__(self, srv):
        self.host = maybe_str(_ffi.string(srv.host))
        self.port = srv.port
        self.priority = srv.priority
        self.weight = srv.weight
        self.ttl = -1


class ares_query_txt_result(AresResult):
    __slots__ = ("text", "ttl")
    type: Final = "TXT"

    def __init__(self, txt_chunk):
        self.text = maybe_str(txt_chunk.text)
        self.ttl = -1


class ares_query_txt_result_chunk(AresResult):
    __slots__ = ("text", "ttl")
    type: Final = "TXT"

    def __init__(self, txt):
        self.text = _ffi.string(txt.txt)
        self.ttl = -1


# Other result types
#


class ares_host_result(AresResult):
    __slots__ = ("name", "aliases", "addresses")

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
            if _ffi.NULL != _lib.ares_inet_ntop(
                hostent.h_addrtype, hostent.h_addr_list[i], buf, _lib.INET6_ADDRSTRLEN
            ):
                self.addresses.append(
                    maybe_str(_ffi.string(buf, _lib.INET6_ADDRSTRLEN))
                )
            i += 1


class ares_nameinfo_result(AresResult):
    __slots__ = ("node", "service")

    def __init__(self, node, service):
        self.node = maybe_str(_ffi.string(node))
        self.service = maybe_str(_ffi.string(service)) if service != _ffi.NULL else None


class ares_addrinfo_node_result(AresResult):
    __slots__ = ("ttl", "flags", "family", "socktype", "protocol", "addr")

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
            if _ffi.NULL != _lib.ares_inet_ntop(
                s.sin_family, _ffi.addressof(s.sin_addr), ip, _lib.INET6_ADDRSTRLEN
            ):
                # (address, port) 2-tuple for AF_INET
                self.addr = (
                    _ffi.string(ip, _lib.INET6_ADDRSTRLEN),
                    socket.ntohs(s.sin_port),
                )
        elif addr.sa_family == socket.AF_INET6:
            self.family = socket.AF_INET6
            s = _ffi.cast("struct sockaddr_in6*", addr)
            if _ffi.NULL != _lib.ares_inet_ntop(
                s.sin6_family, _ffi.addressof(s.sin6_addr), ip, _lib.INET6_ADDRSTRLEN
            ):
                # (address, port, flow info, scope id) 4-tuple for AF_INET6
                self.addr = (
                    _ffi.string(ip, _lib.INET6_ADDRSTRLEN),
                    socket.ntohs(s.sin6_port),
                    s.sin6_flowinfo,
                    s.sin6_scope_id,
                )
        else:
            raise ValueError("invalid sockaddr family")


class ares_addrinfo_cname_result(AresResult):
    __slots__ = ("ttl", "alias", "name")

    def __init__(self, ares_cname):
        self.ttl = ares_cname.ttl
        self.alias = maybe_str(_ffi.string(ares_cname.alias))
        self.name = maybe_str(_ffi.string(ares_cname.name))


class ares_addrinfo_result(AresResult):
    __slots__ = ("cnames", "nodes")

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
)
