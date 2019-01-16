
import pycares
import pyuv
import socket


class DNSResolver(object):
    def __init__(self, loop):
        self._channel = pycares.Channel(sock_state_cb=self._sock_state_cb)
        self.loop = loop
        self._timer = pyuv.Timer(self.loop)
        self._fd_map = {}

    def _sock_state_cb(self, fd, readable, writable):
        if readable or writable:
            if fd not in self._fd_map:
                # New socket
                handle = pyuv.Poll(self.loop, fd)
                handle.fd = fd
                self._fd_map[fd] = handle
            else:
                handle = self._fd_map[fd]
            if not self._timer.active:
                self._timer.start(self._timer_cb, 1.0, 1.0)
            handle.start((pyuv.UV_READABLE if readable else 0) | (pyuv.UV_WRITABLE if writable else 0), self._poll_cb)
        else:
            # Socket is now closed
            handle = self._fd_map.pop(fd)
            handle.close()
            if not self._fd_map:
                self._timer.stop()

    def _timer_cb(self, timer):
        self._channel.process_fd(pycares.ARES_SOCKET_BAD, pycares.ARES_SOCKET_BAD)

    def _poll_cb(self, handle, events, error):
        read_fd = handle.fd
        write_fd = handle.fd
        if error is not None:
            # There was an error, pretend the socket is ready
            self._channel.process_fd(read_fd, write_fd)
            return
        if not events & pyuv.UV_READABLE:
            read_fd = pycares.ARES_SOCKET_BAD
        if not events & pyuv.UV_WRITABLE:
            write_fd = pycares.ARES_SOCKET_BAD
        self._channel.process_fd(read_fd, write_fd)

    def query(self, query_type, name, cb):
        self._channel.query(query_type, name, cb)

    def gethostbyname(self, name, cb):
        self._channel.gethostbyname(name, socket.AF_INET, cb)


if __name__ == '__main__':
    def query_cb(result, error):
        print(result)
        print(error)
    def gethostbyname_cb(result, error):
        print(result)
        print(error)
    loop = pyuv.Loop.default_loop()
    resolver = DNSResolver(loop)
    resolver.query('google.com', pycares.QUERY_TYPE_A, query_cb)
    resolver.query('sip2sip.info', pycares.QUERY_TYPE_SOA, query_cb)
    resolver.gethostbyname('apple.com', gethostbyname_cb)
    loop.run()

