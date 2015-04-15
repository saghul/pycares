import pycares
from gevent import select
from gevent.local import local
import socket


class Channel(object):
    cache = local()
    channel_class = pycares.Channel

    @staticmethod
    def new_cb(key, results):
        def fn(result, error):
            results[key] = result

        return fn

    @staticmethod
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

    @classmethod
    def call(cls, *args, **kwargs):
        """
        args -  'query', 'google.com', pycares.QUERY_TYPE_A
        kwargs:
          a = ('query', 'google.com', pycares.QUERY_TYPE_A),
          b = ('query', 'google.com', pycares.QUERY_TYPE_MX),
        """

        if not hasattr(cls.cache, 'channel'):
            cls.cache.channel = cls.channel_class()

        channel = cls.cache.channel

        if (args and kwargs) or not (args or kwargs):
            raise ValueError('can not use both args and kwargs or none')

        results = {}
        is_args = False

        if args:
            is_args = True
            params = args[1:] + (cls.new_cb(0, results),)
            getattr(channel, args[0])(*params)
        elif kwargs:
            for key, args in kwargs.items():
                params = args[1:] + (cls.new_cb(key, results),)
                getattr(channel, args[0])(*params)

        cls.wait_channel(channel)

        if is_args:
            return results[0]
        else:
            return results

channel = Channel


if __name__ == '__main__':
    for key, result in channel.call(
        host_of_google=('gethostbyname', 'google.com', socket.AF_INET),
        a_of_google=('query', 'google.com', pycares.QUERY_TYPE_A),
        mx_of_gmail=('query', 'gmail.com', pycares.QUERY_TYPE_MX),
    ).items():
        print '%s: ' % key, result
        print '=' * 20

    print 'gethostbyname(google.com): ', channel.call(
        'gethostbyname', 'google.com', socket.AF_INET
    )

    print "Done!"
