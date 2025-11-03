
import asyncio
import socket

import pycares


class DNSResolver(object):
    EVENT_READ = 0
    EVENT_WRITE = 1

    def __init__(self, loop=None):
        self._channel = pycares.Channel(sock_state_cb=self._sock_state_cb)
        self._timer = None
        self._fds = set()
        self.loop = loop or asyncio.get_event_loop()

    def _sock_state_cb(self, fd, readable, writable):
        if readable or writable:
            if readable:
                self.loop.add_reader(fd, self._process_events, fd, self.EVENT_READ)
            if writable:
                self.loop.add_writer(fd, self._process_events, fd, self.EVENT_WRITE)
            self._fds.add(fd)
            if self._timer is None:
                self._timer = self.loop.call_later(1.0, self._timer_cb)
        else:
            # socket is now closed
            self._fds.discard(fd)
            if not self._fds:
                self._timer.cancel()
                self._timer = None

    def _timer_cb(self):
        self._channel.process_fd(pycares.ARES_SOCKET_BAD, pycares.ARES_SOCKET_BAD)
        self._timer = self.loop.call_later(1.0, self._timer_cb)

    def _process_events(self, fd, event):
        if event == self.EVENT_READ:
            read_fd = fd
            write_fd = pycares.ARES_SOCKET_BAD
        elif event == self.EVENT_WRITE:
            read_fd = pycares.ARES_SOCKET_BAD
            write_fd = fd
        else:
            read_fd = write_fd = pycares.ARES_SOCKET_BAD
        self._channel.process_fd(read_fd, write_fd)

    def query(self, query_type, name, cb):
        self._channel.query(query_type, name, cb)

    def close(self):
        """Close the resolver and cleanup resources."""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        for fd in self._fds:
            self.loop.remove_reader(fd)
            self.loop.remove_writer(fd)
        self._fds.clear()
        # Note: The channel will be destroyed safely in a background thread
        # with a 1-second delay to ensure c-ares has completed its cleanup.
        self._channel.close()


async def main():
    def cb(result, error):
        if error:
            print("Error: {}".format(error))
        else:
            print("Query result:")
            print("  Answer section ({} records):".format(len(result.answer)))
            for record in result.answer:
                print("    - Name: {}, Type: {}, TTL: {}s".format(record.name, record.type, record.ttl))
                print("      Data: {}".format(record.data))
            if result.authority:
                print("  Authority section ({} records)".format(len(result.authority)))
            if result.additional:
                print("  Additional section ({} records)".format(len(result.additional)))

    loop = asyncio.get_running_loop()
    resolver = DNSResolver(loop)

    try:
        resolver.query('google.com', pycares.QUERY_TYPE_A, cb)
        resolver.query('sip2sip.info', pycares.QUERY_TYPE_SOA, cb)

        # Give some time for queries to complete
        await asyncio.sleep(2)
    finally:
        resolver.close()


if __name__ == '__main__':
    asyncio.run(main())

