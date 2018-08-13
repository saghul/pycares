
import pycares
import select
import socket


class DNSResolver(object):
    def __init__(self):
        self._channel = pycares.Channel(sock_state_cb=self._sock_state_cb)
        self.poll = select.epoll() if hasattr(select, "epoll") else select.poll()
        self._fd_map = set()

    def _sock_state_cb(self, fd, readable, writable):
        print("fd {} read {} write {}".format(fd, readable, writable))
        if readable or writable:
            event = (select.POLLIN if readable else 0) | (select.POLLOUT if writable else 0)
            if fd not in self._fd_map:
                # New socket
                print("register %d" % fd)
                self.poll.register(fd, event)
                self._fd_map.add(fd)
            else:
                print("modify %d" % fd)
                self.poll.modify(fd, event)
        else:
            # Socket is now closed
            self._fd_map.remove(fd)
            print("unregister %d" % fd)
            self.poll.unregister(fd)

    def wait_channel(self):
        while True:
            if not self._fd_map:
                break
            timeout = self._channel.timeout(1.0)
            if not timeout:
                self._channel.process_fd(pycares.ARES_SOCKET_BAD, pycares.ARES_SOCKET_BAD)
                continue
            for fd, event in self.poll.poll(timeout):
                if event & (select.POLLIN | select.POLLPRI):
                    self._channel.process_fd(fd, pycares.ARES_SOCKET_BAD)
                if event & select.POLLOUT:
                    self._channel.process_fd(pycares.ARES_SOCKET_BAD, fd)

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
    resolver = DNSResolver()
    resolver.query('google.com', pycares.QUERY_TYPE_A, query_cb)
    resolver.query('facebook.com', pycares.QUERY_TYPE_A, query_cb)
    resolver.query('sip2sip.info', pycares.QUERY_TYPE_SOA, query_cb)
    resolver.gethostbyname('apple.com', gethostbyname_cb)
    resolver.wait_channel()
