.. _utils:

=================
Utility functions
=================


.. py:function:: pycares.reverse_address(ip_adress)

    :param string ip_address: IP address to be reversed.

    Returns the reversed representation of an IP address, usually used when
    doing PTR queries.

    Example:

    ::

        pycares.reverse_address('1.2.3.4')
        '4.3.2.1.in-addr.arpa'

        pycares.reverse_address('2a03:2880:10:cf01:face:b00c::')
        '0.0.0.0.0.0.0.0.c.0.0.b.e.c.a.f.1.0.f.c.0.1.0.0.0.8.8.2.3.0.a.2.ip6.arpa'

