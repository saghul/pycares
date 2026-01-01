
import pycares
import sys


# Map query type integers to string names for display
QUERY_TYPE_NAMES = {
    pycares.QUERY_TYPE_A: 'A',
    pycares.QUERY_TYPE_AAAA: 'AAAA',
    pycares.QUERY_TYPE_ANY: 'ANY',
    pycares.QUERY_TYPE_CAA: 'CAA',
    pycares.QUERY_TYPE_CNAME: 'CNAME',
    pycares.QUERY_TYPE_HTTPS: 'HTTPS',
    pycares.QUERY_TYPE_MX: 'MX',
    pycares.QUERY_TYPE_NAPTR: 'NAPTR',
    pycares.QUERY_TYPE_NS: 'NS',
    pycares.QUERY_TYPE_PTR: 'PTR',
    pycares.QUERY_TYPE_SOA: 'SOA',
    pycares.QUERY_TYPE_SRV: 'SRV',
    pycares.QUERY_TYPE_TLSA: 'TLSA',
    pycares.QUERY_TYPE_TXT: 'TXT',
    pycares.QUERY_TYPE_URI: 'URI',
}


def format_record(record):
    """Format a DNS record for display."""
    type_name = QUERY_TYPE_NAMES.get(record.type, str(record.type))
    prefix = '%s\t\t%d\tIN\t%s' % (record.name, record.ttl, type_name)
    data = record.data

    if record.type == pycares.QUERY_TYPE_A:
        return '%s\t%s' % (prefix, data.addr)
    elif record.type == pycares.QUERY_TYPE_AAAA:
        return '%s\t%s' % (prefix, data.addr)
    elif record.type == pycares.QUERY_TYPE_CAA:
        return '%s\t%d %s "%s"' % (prefix, data.critical, data.tag, data.value)
    elif record.type == pycares.QUERY_TYPE_CNAME:
        return '%s\t%s' % (prefix, data.cname)
    elif record.type == pycares.QUERY_TYPE_HTTPS:
        params_str = ' '.join('%s=%s' % (k, v) for k, v in data.params)
        return '%s\t%d %s %s' % (prefix, data.priority, data.target, params_str)
    elif record.type == pycares.QUERY_TYPE_MX:
        return '%s\t%d %s' % (prefix, data.priority, data.exchange)
    elif record.type == pycares.QUERY_TYPE_NAPTR:
        return '%s\t%d %d "%s" "%s" "%s" %s' % (
            prefix, data.order, data.preference, data.flags,
            data.service, data.regexp, data.replacement
        )
    elif record.type == pycares.QUERY_TYPE_NS:
        return '%s\t%s' % (prefix, data.nsdname)
    elif record.type == pycares.QUERY_TYPE_PTR:
        return '%s\t%s' % (prefix, data.dname)
    elif record.type == pycares.QUERY_TYPE_SOA:
        return '%s\t%s %s %d %d %d %d %d' % (
            prefix, data.mname, data.rname, data.serial,
            data.refresh, data.retry, data.expire, data.minimum
        )
    elif record.type == pycares.QUERY_TYPE_SRV:
        return '%s\t%d %d %d %s' % (
            prefix, data.priority, data.weight, data.port, data.target
        )
    elif record.type == pycares.QUERY_TYPE_TLSA:
        return '%s\t%d %d %d %s' % (
            prefix, data.cert_usage, data.selector,
            data.matching_type, data.cert_association_data.hex()
        )
    elif record.type == pycares.QUERY_TYPE_TXT:
        # TXT data is bytes in 5.0
        text = data.data.decode('utf-8', errors='replace')
        return '%s\t"%s"' % (prefix, text)
    elif record.type == pycares.QUERY_TYPE_URI:
        return '%s\t%d %d "%s"' % (prefix, data.priority, data.weight, data.target)
    else:
        return '%s\t%s' % (prefix, data)


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

        for record in result.answer:
            parts.append(format_record(record))

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

channel.query(hostname, query_type, callback=cb)
channel.wait()
