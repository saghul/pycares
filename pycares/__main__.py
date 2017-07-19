
import pycares
import select
import socket
import sys


def wait_channel(channel):
    while True:
        read_fds, write_fds = channel.getsock()
        if not read_fds and not write_fds:
            break
        timeout = channel.timeout()
        if not timeout:
            channel.process_fd(pycares.ARES_SOCKET_BAD, pycares.ARES_SOCKET_BAD)
            continue
        rlist, wlist, xlist = select.select(read_fds, write_fds, [], timeout)
        for fd in rlist:
            channel.process_fd(fd, pycares.ARES_SOCKET_BAD)
        for fd in wlist:
            channel.process_fd(pycares.ARES_SOCKET_BAD, fd)


def cb(result, error):
    if error is not None:
        print('Error: (%d) %s' % (error, pycares.errno.strerror(error)))
    else:
        print(result)


channel = pycares.Channel()

if len(sys.argv) not in (2, 3):
    print('Invalid arguments! Usage: python -m pycares [query_type] hostname')
    sys.exit(1)

if len(sys.argv) == 2:
    _, hostname = sys.argv
    qtype = 'A'
else:
    _, qtype, hostname = sys.argv

try:
    query_type = getattr(pycares, 'QUERY_TYPE_%s' % qtype.upper())
except Exception:
    print('Invalid query type: %s' % qtype)
    sys.exit(1)

channel.query(hostname, query_type, cb)
wait_channel(channel)
