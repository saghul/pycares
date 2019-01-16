
import pycares
import select
import socket


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


if __name__ == '__main__':
    def cb(result, error):
        print(result)
        print(error)
    channel = pycares.Channel()
    channel.gethostbyname('google.com', socket.AF_INET, cb)
    channel.query('google.com', pycares.QUERY_TYPE_A, cb)
    channel.query('sip2sip.info', pycares.QUERY_TYPE_SOA, cb)
    wait_channel(channel)
    print('Done!')

