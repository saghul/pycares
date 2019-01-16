
import collections.abc
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
        parts = [
            ';; QUESTION SECTION:',
            ';%s\t\t\tIN\t%s' % (hostname, qtype.upper()),
            '',
            ';; ANSWER SECTION:'
        ]

        if not isinstance(result, collections.abc.Iterable):
            result = [result]

        for r in result:
            txt = '%s\t\t%d\tIN\t%s' % (hostname, r.ttl, qtype.upper())
            if query_type == pycares.QUERY_TYPE_A or query_type == pycares.QUERY_TYPE_AAAA:
                parts.append('%s\t%s' % (txt, r.host))
            elif query_type == pycares.QUERY_TYPE_CNAME:
                parts.append('%s\t%s' % (txt, r.cname))
            elif query_type == pycares.QUERY_TYPE_MX:
                parts.append('%s\t%d %s' % (txt, r.priority, r.host))
            elif query_type == pycares.QUERY_TYPE_NAPTR:
                parts.append('%s\t%d %d "%s" "%s" "%s" %s' % (txt, r.order, r.preference, r.flags, r.service, r.regex, r.replacement))
            elif query_type == pycares.QUERY_TYPE_NS:
                parts.append('%s\t%s' % (txt, r.host))
            elif query_type == pycares.QUERY_TYPE_PTR:
                parts.append('%s\t%s' % (txt, r.name))
            elif query_type == pycares.QUERY_TYPE_SOA:
                parts.append('%s\t%s %s %d %d %d %d %d' % (txt, r.nsname, r.hostmaster, r.serial, r.refresh, r.retry, r.expires, r.minttl))
            elif query_type == pycares.QUERY_TYPE_SRV:
                parts.append('%s\t%d %d %d %s' % (txt, r.priority, r.weight, r.port, r.host))
            elif query_type == pycares.QUERY_TYPE_TXT:
                parts.append('%s\t"%s"' % (txt, r.text))

        print('\n'.join(parts))


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
