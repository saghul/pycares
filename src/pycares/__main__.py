
import collections.abc
import pycares
import sys


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
            txt = '%s\t\t%d\tIN\t%s' % (hostname, r.ttl, r.type)
            if r.type in ('A', 'AAAA'):
                parts.append('%s\t%s' % (txt, r.host))
            elif r.type == 'CAA':
                parts.append('%s\t%d %s "%s"' % (txt, r.critical, r.property, r.value))
            elif r.type == 'CNAME':
                parts.append('%s\t%s' % (txt, r.cname))
            elif r.type == 'MX':
                parts.append('%s\t%d %s' % (txt, r.priority, r.host))
            elif r.type == 'NAPTR':
                parts.append('%s\t%d %d "%s" "%s" "%s" %s' % (txt, r.order, r.preference, r.flags, r.service, r.regex, r.replacement))
            elif r.type == 'NS':
                parts.append('%s\t%s' % (txt, r.host))
            elif r.type == 'PTR':
                parts.append('%s\t%s' % (txt, r.name))
            elif r.type == 'SOA':
                parts.append('%s\t%s %s %d %d %d %d %d' % (txt, r.nsname, r.hostmaster, r.serial, r.refresh, r.retry, r.expires, r.minttl))
            elif r.type == 'SRV':
                parts.append('%s\t%d %d %d %s' % (txt, r.priority, r.weight, r.port, r.host))
            elif r.type == 'TXT':
                parts.append('%s\t"%s"' % (txt, r.text))

        print('\n'.join(parts))


channel = pycares.Channel(event_thread=True)

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
channel.wait()
