
import pycares
import selectors


class DNSResolver(object):
    def __init__(self):
        self._channel = pycares.Channel(sock_state_cb=self._sock_state_cb)
        self.poll = selectors.DefaultSelector()
        self._fd_map = set()

    def _sock_state_cb(self, fd, readable, writable):
        print("fd {} read {} write {}".format(fd, readable, writable))
        if readable or writable:
            event = (selectors.EVENT_READ if readable else 0) | (selectors.EVENT_WRITE if writable else 0)
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
            for key, event in self.poll.select(timeout):
                read_fd = key.fd if event & selectors.EVENT_READ else pycares.ARES_SOCKET_BAD
                write_fd = key.fd if event & selectors.EVENT_WRITE else pycares.ARES_SOCKET_BAD
                self._channel.process_fd(read_fd, write_fd)

    def query(self, query_type, name, cb):
        self._channel.query(query_type, name, cb)

    def close(self):
        """Close the resolver and cleanup resources."""
        for fd in list(self._fd_map):
            self.poll.unregister(fd)
        self._fd_map.clear()
        self.poll.close()
        self._channel.close()


if __name__ == '__main__':
    def query_cb(result, error):
        if error:
            print("Error: {}".format(error))
        else:
            print("DNS Result:")
            print("  Answer: {} records".format(len(result.answer)))
            for record in result.answer:
                print("    - {} (TTL: {}s): {}".format(record.name, record.ttl, record.data))
            if result.authority:
                print("  Authority: {} records".format(len(result.authority)))
            if result.additional:
                print("  Additional: {} records".format(len(result.additional)))
    resolver = DNSResolver()
    try:
        resolver.query('google.com', pycares.QUERY_TYPE_A, query_cb)
        resolver.query('google.com', pycares.QUERY_TYPE_AAAA, query_cb)
        resolver.query('facebook.com', pycares.QUERY_TYPE_A, query_cb)
        resolver.query('sip2sip.info', pycares.QUERY_TYPE_SOA, query_cb)
        resolver.wait_channel()
    finally:
        resolver.close()

