
from _pycares_cffi import ffi as _ffi, lib as _lib
import _cffi_backend  # hint for bundler tools

from . import errno
from .errno import ARES_SUCCESS

import socket
import math
import functools
import sys


IS_PY2 = sys.version_info[0] < 3

if IS_PY2:
    b2s = lambda s: s
    s2b = lambda s: s
    _ffi_string = _ffi.string
else:
    def b2s(b):
        return b.decode('utf-8')
    def s2b(s):
        return s.encode('utf-8')
    _ffi_string = lambda r, maxlen=-1: b2s(_ffi.string(r, maxlen))


exported_pycares_symbols = [
    # Flag values
    'ARES_FLAG_USEVC',
    'ARES_FLAG_PRIMARY',
    'ARES_FLAG_IGNTC',
    'ARES_FLAG_NORECURSE',
    'ARES_FLAG_STAYOPEN',
    'ARES_FLAG_NOSEARCH',
    'ARES_FLAG_NOALIASES',
    'ARES_FLAG_NOCHECKRESP',

    # Nameinfo flag values
    'ARES_NI_NOFQDN',
    'ARES_NI_NUMERICHOST',
    'ARES_NI_NAMEREQD',
    'ARES_NI_NUMERICSERV',
    'ARES_NI_DGRAM',
    'ARES_NI_TCP',
    'ARES_NI_UDP',
    'ARES_NI_SCTP',
    'ARES_NI_DCCP',
    'ARES_NI_NUMERICSCOPE',
    'ARES_NI_LOOKUPHOST',
    'ARES_NI_LOOKUPSERVICE',
    'ARES_NI_IDN',
    'ARES_NI_IDN_ALLOW_UNASSIGNED',
    'ARES_NI_IDN_USE_STD3_ASCII_RULES',

    # Bad socket
    'ARES_SOCKET_BAD',
]

for symbol in exported_pycares_symbols:
    globals()[symbol] = getattr(_lib, symbol)


exported_pycares_symbols_map = {
    # Query types
    "QUERY_TYPE_A" : "T_A",
    "QUERY_TYPE_AAAA" : "T_AAAA",
    "QUERY_TYPE_CNAME" : "T_CNAME",
    "QUERY_TYPE_MX" : "T_MX",
    "QUERY_TYPE_NAPTR" : "T_NAPTR",
    "QUERY_TYPE_NS" : "T_NS",
    "QUERY_TYPE_PTR" : "T_PTR",
    "QUERY_TYPE_SOA" : "T_SOA",
    "QUERY_TYPE_SRV" : "T_SRV",
    "QUERY_TYPE_TXT" : "T_TXT",
}

for k, v in exported_pycares_symbols_map.items():
    globals()[k] = getattr(_lib, v)


globals()['ARES_VERSION'] = _ffi_string(_lib.ares_version(_ffi.NULL))


PYCARES_ADDRTTL_SIZE = 256


class Error(Exception):
    pass


class Warning(Exception):
    pass


class InterfaceError(Error):
    pass


class AresError(Error):
    pass


class NotSupportedError(Exception):
    pass


def check_channel(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwds):
        if not self.channel:
            raise AresError("Channel has already been destroyed")
        return f(self, *args, **kwds)
    return wrapper

# callback helpers

_global_set = set()

@_ffi.callback("void (void *data, ares_socket_t socket_fd, int readable, int writable )")
def _sock_state_cb(data, socket_fd, readable, writable):
    sock_state_cb = _ffi.from_handle(data)
    sock_state_cb(socket_fd, readable, writable)
    _global_set.discard(data)

@_ffi.callback("void (void *arg, int status, int timeouts, struct hostent *hostent)")
def _host_cb(arg, status, timeouts, hostent):
    callback = _ffi.from_handle(arg)
    if status != _lib.ARES_SUCCESS:
        result = None
    else:
        result = ares_host_result(hostent)
        status = None

    callback(result, status)
    _global_set.discard(arg)

@_ffi.callback("void (void *arg, int status, int timeouts, char *node, char *service)")
def _nameinfo_cb(arg, status, timeouts, node, service):
    callback = _ffi.from_handle(arg)
    if status != _lib.ARES_SUCCESS:
        result = None
    else:
        result = ares_nameinfo_result(node, service)
        status = None

    callback(result, status)
    _global_set.discard(arg)

@_ffi.callback("void (void *arg, int status, int timeouts, unsigned char *abuf, int alen)")
def _query_cb(arg, status, timeouts, abuf, alen):
    result = None
    callback, query_type = _ffi.from_handle(arg)
    if status == _lib.ARES_SUCCESS:
        if query_type == _lib.T_A:
            addrttls = _ffi.new("struct ares_addrttl[]", PYCARES_ADDRTTL_SIZE)
            naddrttls = _ffi.new("int*", PYCARES_ADDRTTL_SIZE)
            parse_status = _lib.ares_parse_a_reply(abuf, alen, _ffi.NULL, addrttls, naddrttls)
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = [ares_query_simple_result(addrttls[i]) for i in range(naddrttls[0])]
                status = None

        elif query_type == _lib.T_AAAA:
            addrttls = _ffi.new("struct ares_addr6ttl[]", PYCARES_ADDRTTL_SIZE)
            naddrttls = _ffi.new("int*", PYCARES_ADDRTTL_SIZE)
            parse_status = _lib.ares_parse_aaaa_reply(abuf, alen, _ffi.NULL, addrttls, naddrttls)
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = [ares_query_simple_result(addrttls[i]) for i in range(naddrttls[0])]
                status = None

        elif query_type == _lib.T_CNAME:
            host = _ffi.new("struct hostent **")
            parse_status = _lib.ares_parse_a_reply(abuf, alen, host, _ffi.NULL, _ffi.NULL)
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = ares_query_cname_result(host[0])
                _lib.ares_free_hostent(host[0])
                status = None

        elif query_type == _lib.T_MX:
            mx_reply = _ffi.new("struct ares_mx_reply **")
            parse_status = _lib.ares_parse_mx_reply(abuf, alen, mx_reply);
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = []
                mx_reply_ptr = _ffi.new("struct ares_mx_reply **")
                mx_reply_ptr[0] = mx_reply[0]
                while True:
                    if mx_reply_ptr[0] == _ffi.NULL:
                        break
                    result.append(ares_query_mx_result(mx_reply[0]))
                    mx_reply_ptr[0] = mx_reply_ptr[0].next
                _lib.ares_free_data(mx_reply)
                status = None

        elif query_type == _lib.T_NAPTR:
            naptr_reply = _ffi.new("struct ares_naptr_reply **")
            parse_status = _lib.ares_parse_naptr_reply(abuf, alen, naptr_reply);
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = []
                naptr_reply_ptr = _ffi.new("struct ares_naptr_reply **")
                naptr_reply_ptr[0] = naptr_reply[0]
                while True:
                    if naptr_reply_ptr[0] == _ffi.NULL:
                        break
                    result.append(ares_query_naptr_result(naptr_reply[0]))
                    naptr_reply_ptr[0] = naptr_reply_ptr[0].next
                _lib.ares_free_data(naptr_reply)
                status = None

        elif query_type == _lib.T_NS:
            hostent = _ffi.new("struct hostent **")
            parse_status = _lib.ares_parse_ns_reply(abuf, alen, hostent);
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = []
                host = hostent[0]
                for i in range(100):
                    if host.h_aliases[i] == _ffi.NULL:
                        break
                    result.append(ares_query_ns_result(host.h_aliases[i]))

                _lib.ares_free_hostent(host)
                status = None

        elif query_type == _lib.T_PTR:
            hostent = _ffi.new("struct hostent **")
            hostttl = _ffi.new("int*", PYCARES_ADDRTTL_SIZE)
            parse_status = _lib.ares_parse_ptr_reply(abuf, alen, _ffi.NULL, 0, socket.AF_UNSPEC, hostent, hostttl);
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                aliases = []
                i = 0
                terminator = _ffi.cast('char*', _ffi.NULL)
                while hostent[0].h_aliases[i] != terminator:
                    aliases.append(_ffi.string(hostent[0].h_aliases[i]))
                    i += 1
                result = ares_query_ptr_result(hostent[0], hostttl[0], aliases)
                _lib.ares_free_hostent(hostent[0])
                status = None

        elif query_type == _lib.T_SOA:
            soa_reply = _ffi.new("struct ares_soa_reply **")
            parse_status = _lib.ares_parse_soa_reply(abuf, alen, soa_reply);
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = ares_query_soa_result(soa_reply[0])
                _lib.ares_free_data(soa_reply[0])
                status = None

        elif query_type == _lib.T_SRV:
            srv_reply = _ffi.new("struct ares_srv_reply **")
            parse_status = _lib.ares_parse_srv_reply(abuf, alen, srv_reply);
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = []
                srv_reply_ptr = _ffi.new("struct ares_srv_reply **")
                srv_reply_ptr[0] = srv_reply[0]
                while True:
                    if srv_reply_ptr[0] == _ffi.NULL:
                        break
                    result.append(ares_query_srv_result(srv_reply_ptr[0]))
                    srv_reply_ptr[0] = srv_reply_ptr[0].next
                _lib.ares_free_data(srv_reply[0])
                status = None

        elif query_type == _lib.T_TXT:
            txt_reply = _ffi.new("struct ares_txt_ext **")
            parse_status = _lib.ares_parse_txt_reply_ext(abuf, alen, txt_reply);
            if parse_status != ARES_SUCCESS:
                result = None
                status = parse_status
            else:
                result = []
                txt_reply_ptr = _ffi.new("struct ares_txt_ext **")
                txt_reply_ptr[0] = txt_reply[0]
                tmp_obj = None
                while True:
                    if txt_reply_ptr[0] == _ffi.NULL:
                        if tmp_obj is not None:
                            result.append(tmp_obj)
                        break
                    if txt_reply_ptr[0].record_start == 1:
                        if tmp_obj is not None:
                            result.append(tmp_obj)
                        tmp_obj = ares_query_txt_result(txt_reply_ptr[0])
                    else:
                        new_chunk = ares_query_txt_result(txt_reply_ptr[0])
                        tmp_obj.text += new_chunk.text
                    txt_reply_ptr[0] = txt_reply_ptr[0].next
                _lib.ares_free_data(txt_reply[0])
                status = None
        else:
            raise ValueError("invalid query type specified")

    callback(result, status)
    _global_set.discard(arg)


class Channel(object):
    def __init__(self, flags = -1, timeout = -1.0,
                 tries = -1, ndots = -1, tcp_port = -1, udp_port = -1,
                 servers = None, domains = None, lookups = None, sock_state_cb = None,
                 socket_send_buffer_size = -1, socket_receive_buffer_size = -1, rotate = False,
                 local_ip = None, local_dev = None):

        channel = _ffi.new("ares_channel *")
        options = _ffi.new("struct ares_options *")
        optmask = 0

        if flags != -1:
            options.flags = flags
            optmask = optmask | _lib.ARES_OPT_FLAGS

        if timeout != -1:
            options.timeout = int(timeout * 1000)
            optmask = optmask | _lib.ARES_OPT_TIMEOUTMS

        if tries != -1:
            options.tries = tries
            optmask = optmask |  _lib.ARES_OPT_TRIES

        if ndots != -1:
            options.ndots = ndots
            optmask = optmask |  _lib.ARES_OPT_NDOTS

        if tcp_port != -1:
            options.tcp_port = tcp_port
            optmask = optmask |  _lib.ARES_OPT_TCP_PORT

        if udp_port != -1:
            options.udp_port = udp_port
            optmask = optmask |  _lib.ARES_OPT_UDP_PORT

        if socket_send_buffer_size != -1:
            options.socket_send_buffer_size = socket_send_buffer_size
            optmask = optmask |  _lib.ARES_OPT_SOCK_SNDBUF

        if socket_receive_buffer_size != -1:
            options.socket_receive_buffer_size = socket_receive_buffer_size
            optmask = optmask |  _lib.ARES_OPT_SOCK_RCVBUF

        if sock_state_cb:
            if not callable(sock_state_cb):
                raise AresError("sock_state_cb is not callable")

            userdata = _ffi.new_handle(sock_state_cb)
            _global_set.add(userdata)     # must keep this alive!
            options.sock_state_cb = _sock_state_cb
            options.sock_state_cb_data = userdata
            optmask = optmask |  _lib.ARES_OPT_SOCK_STATE_CB

        if lookups:
            options.lookups = lookups
            optmask = optmask |  _lib.ARES_OPT_LOOKUPS

        if domains:
            strs = [_ffi.new("char[]", s2b(i)) for i in domains]
            c = _ffi.new("char *[%d]" % (len(domains) + 1))
            for i in range(len(domains)):
               c[i] = strs[i]

            options.domains = c
            options.ndomains = len(domains)
            optmask = optmask |  _lib.ARES_OPT_DOMAINS

        if rotate == True:
            optmask = optmask |  _lib.ARES_OPT_ROTATE

        r = _lib.ares_init_options(channel, options, optmask)
        if r != _lib.ARES_SUCCESS:
            raise AresError()

        self.channel = channel[0]

        if servers:
            self._set_servers(servers)

        if local_ip:
            self.set_local_ip(local_ip)

        if local_dev:
            self.set_local_dev(local_dev)

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self.channel:
            _lib.ares_destroy(self.channel)
            self.channel = None

    @check_channel
    def cancel(self):
        _lib.ares_cancel(self.channel)

    @check_channel
    def _set_servers(self, servers):
        c = _ffi.new("struct ares_addr_node[%d]" % len(servers))
        for i in range(len(servers)):
            if 1 == _lib.ares_inet_pton(socket.AF_INET, s2b(servers[i]), _ffi.addressof(c[i].addr.addr4)):
                c[i].family = socket.AF_INET
            elif 1 == _lib.ares_inet_pton(socket.AF_INET6, s2b(servers[i]), _ffi.addressof(c[i].addr.addr6)):
                c[i].family = socket.AF_INET6
            else:
                raise ValueError("invalid IP address")

            if i > 0:
                c[i - 1].next = _ffi.addressof(c[i])

        r = _lib.ares_set_servers(self.channel, c)
        if r != _lib.ARES_SUCCESS:
            raise AresError()

    @check_channel
    def _get_servers(self):
        servers = _ffi.new("struct ares_addr_node **")

        r = _lib.ares_get_servers(self.channel, servers)
        if r != ARES_SUCCESS:
            raise AresError(errno.strerror(r))

        server_list = []
        server = _ffi.new("struct ares_addr_node **", servers[0])
        while True:
            if server == _ffi.NULL:
                break

            ip = _ffi.new("char []", _lib.INET6_ADDRSTRLEN)
            if _ffi.NULL != _lib.ares_inet_ntop(server.family, _ffi.addressof(server.addr), ip, _lib.INET6_ADDRSTRLEN):
                server_list.append(_ffi_string(ip, _lib.INET6_ADDRSTRLEN))

            server = server.next

        return server_list

    servers = property(_get_servers, _set_servers)

    @check_channel
    def getsock(self):
        rfds = []
        wfds = []
        socks = _ffi.new("ares_socket_t [%d]" % _lib.ARES_GETSOCK_MAXNUM)
        bitmask = _lib.ares_getsock(self.channel, socks, _lib.ARES_GETSOCK_MAXNUM)
        for i in range(_lib.ARES_GETSOCK_MAXNUM):
            if bitmask & (1 << i):
                rfds.append(socks[i])
            if bitmask & (1 << (i + _lib.ARES_GETSOCK_MAXNUM)):
                wfds.append(socks[i])

        return rfds, wfds


    @check_channel
    def process_fd(self, read_fd, write_fd):
        _lib.ares_process_fd(self.channel, _ffi.cast("ares_socket_t", read_fd), _ffi.cast("ares_socket_t", write_fd))

    @check_channel
    def timeout(self, t = -1):
        maxtv = _ffi.NULL
        tv = _ffi.new("struct timeval*")

        if t >= 0.0:
            maxtv = _ffi.new("struct timeval*")
            maxtv.tv_sec = int(math.floor(t))
            maxtv.tv_usec = int(math.fmod(t, 1.0) * 1000000)
        elif t == -1:
            pass
        else:
            raise ValueError("timeout needs to be a positive number")

        _lib.ares_timeout(self.channel, maxtv, tv)

        return (tv.tv_sec + tv.tv_usec / 1000000.0)

    @check_channel
    def gethostbyaddr(self, name, callback):
        if not callable(callback):
            raise TypeError("a callable is required")

        addr4 = _ffi.new("struct in_addr*")
        addr6 = _ffi.new("struct ares_in6_addr*")
        if 1 == _lib.ares_inet_pton(socket.AF_INET,s2b(name), (addr4)):
            address = addr4
            family = socket.AF_INET
        elif 1 == _lib.ares_inet_pton(socket.AF_INET6, s2b(name), (addr6)):
            address = addr6
            family = socket.AF_INET6
        else:
            raise ValueError("invalid IP address")

        userdata = _ffi.new_handle(callback)
        _global_set.add(userdata)
        _lib.ares_gethostbyaddr(self.channel, (address), _ffi.sizeof(address[0]), family, _host_cb, userdata)


    @check_channel
    def gethostbyname(self, name, family, callback):
        if not callable(callback):
            raise TypeError("a callable is required")


        userdata = _ffi.new_handle(callback)
        _global_set.add(userdata)
        _lib.ares_gethostbyname(self.channel, s2b(name), family, _host_cb, userdata)

    def query(self, name, query_type, callback):
        if not callable(callback):
            raise TypeError("a callable is required")

        if query_type not in (_lib.T_A, _lib.T_AAAA, _lib.T_CNAME, _lib.T_MX, _lib.T_NAPTR, _lib.T_NS, _lib.T_PTR, _lib.T_SOA, _lib.T_SRV, _lib.T_TXT):
            raise ValueError("invalid query type specified")


        userdata = _ffi.new_handle((callback, query_type))
        _global_set.add(userdata)
        _lib.ares_query(self.channel, s2b(name), _lib.C_IN, query_type, _query_cb, userdata)

    @check_channel
    def set_local_ip(self, ip):
        addr4 = _ffi.new("struct in_addr*")
        addr6 = _ffi.new("struct ares_in6_addr*")
        if 1 == _lib.ares_inet_pton(socket.AF_INET, s2b(ip), addr4):
            _lib.ares_set_local_ip4(self.channel, socket.ntohl(addr4.s_addr))
        elif 1 == _lib.ares_inet_pton(socket.AF_INET6, s2b(ip), addr6):
            _lib.ares_set_local_ip6(self.channel, addr6)
        else:
            raise ValueError("invalid IP address")

    @check_channel
    def getnameinfo(self, ip_port, flags, callback):
        if not callable(callback):
            raise AresError("a callable is required")

        ip, port = ip_port

        if port < 0 or port > 65535:
            raise ValueError("port must be between 0 and 65535")

        sa4 = _ffi.new("struct sockaddr_in*")
        sa6 = _ffi.new("struct sockaddr_in6*")

        if 1 == _lib.ares_inet_pton(socket.AF_INET, s2b(ip), _ffi.addressof(sa4.sin_addr)):
            sa4.sin_family = socket.AF_INET
            sa4.sin_port = socket.htons(port)
            sa = sa4
        elif 1 == _lib.ares_inet_pton(socket.AF_INET6, s2b(ip), _ffi.addressof(sa6.sin6_addr)):
            sa6.sin6_family = socket.AF_INET6
            sa6.sin6_port = socket.htons(port)
            sa = sa6
        else:
            raise ValueError("invalid IP address")

        userdata = _ffi.new_handle(callback)
        _global_set.add(userdata)
        _lib.ares_getnameinfo(self.channel, _ffi.cast("struct sockaddr*", sa), _ffi.sizeof(sa[0]), flags, _nameinfo_cb, userdata)

    @check_channel
    def set_local_dev(self, dev):
        _lib.ares_set_local_dev(self.channel, dev)


class ares_host_result(object):
    def __init__(self, hostent):
        self.name = _ffi_string(hostent.h_name)
        self.aliases = []
        self.addresses = []
        for i in range(100):
            if hostent.h_aliases[i] == _ffi.NULL:
                break
            self.aliases.append(_ffi_string(hostent.h_aliases[i]))

        for i in range(100):
            if hostent.h_addr_list[i] == _ffi.NULL:
                break

            buf = _ffi.new("char[]", _lib.INET6_ADDRSTRLEN)
            if _ffi.NULL != _lib.ares_inet_ntop(hostent.h_addrtype, hostent.h_addr_list[i], buf, _lib.INET6_ADDRSTRLEN):
                self.addresses.append(_ffi_string(buf, _lib.INET6_ADDRSTRLEN))


class ares_query_simple_result(object):
    def __init__(self, ares_addrttl):
        buf = _ffi.new("char[]", _lib.INET6_ADDRSTRLEN)
        if _ffi.typeof(ares_addrttl) is _ffi.typeof("struct ares_addrttl"):
            _lib.ares_inet_ntop(socket.AF_INET, _ffi.addressof(ares_addrttl.ipaddr), buf, _lib.INET6_ADDRSTRLEN)
        elif _ffi.typeof(ares_addrttl) is _ffi.typeof("struct ares_addr6ttl"):
            _lib.ares_inet_ntop(socket.AF_INET6, _ffi.addressof(ares_addrttl.ip6addr), buf, _lib.INET6_ADDRSTRLEN)
        else:
            raise TypeError()

        self.host = _ffi_string(buf, _lib.INET6_ADDRSTRLEN)
        self.ttl = ares_addrttl.ttl


class ares_query_cname_result(object):
    def __init__(self, host):
        self.cname = _ffi_string(host.h_name)
        self.ttl = None


class ares_query_mx_result(object):
    def __init__(self, mx):
        self.host = _ffi_string(mx.host)
        self.priority = mx.priority
        self.ttl = mx.ttl


class ares_query_naptr_result(object):
    def __init__(self, naptr):
        self.order = naptr.order
        self.preference = naptr.preference
        self.flags = _ffi_string(naptr.flags)
        self.service = _ffi_string(naptr.service)
        self.regex = _ffi_string(naptr.regexp)
        self.replacement = _ffi_string(naptr.replacement)
        self.ttl = naptr.ttl


class ares_query_ns_result(object):
    def __init__(self, ns):
        self.host = _ffi_string(ns)
        self.ttl = None


class ares_query_ptr_result(object):
    def __init__(self, hostent, ttl, aliases):
        self.name = _ffi_string(hostent.h_name)
        self.ttl = ttl
        self.aliases = aliases


class ares_query_soa_result(object):
    def __init__(self, soa):
        self.nsname = _ffi_string(soa.nsname)
        self.hostmaster = _ffi_string(soa.hostmaster)
        self.serial = soa.serial
        self.refresh = soa.refresh
        self.retry = soa.retry
        self.expires = soa.expire
        self.minttl = soa.minttl
        self.ttl = soa.ttl


class  ares_query_srv_result(object):
    def __init__(self, srv):
        self.host = _ffi_string(srv.host)
        self.port = srv.port
        self.priority = srv.priority
        self.weight = srv.weight
        self.ttl = srv.ttl


class ares_query_txt_result(object):
    def __init__(self, txt):
        self.text = _ffi.string(txt.txt)
        self.ttl = txt.ttl


class ares_nameinfo_result(object):
    def __init__(self, node, service):
        self.node = _ffi_string(node)
        self.service = _ffi_string(service) if service != _ffi.NULL else None


def reverse_address(ip):
    """Get reverse representation of an IP address"""
    name = _ffi.new("char []", 128)
    if _ffi.NULL == _lib.reverse_address(s2b(ip), name):
        raise ValueError("invalid IP address")
    return _ffi_string(name, 128)


if _lib.ARES_SUCCESS != _lib.ares_library_init(_lib.ARES_LIB_INIT_ALL):
    assert False

#_lib.ares_library_cleanup()
