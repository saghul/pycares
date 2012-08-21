.. _Channel:


.. currentmodule:: pycares


============
Ares Channel
============


.. py:class:: pycares.Channel(flags, timeout, tries, ndots, tcp_port, udp_port, servers, domains, lookups, sock_state_cb)

    :param int flags: Flags controlling the behavior of the resolver. See ``constants``
        for available values.

    :param float timeout: The number of seconds each name server is given to respond to
        a query on the first try. The default is five seconds.

    :param int tries: The number of tries the resolver will try contacting each name
        server before giving up. The default is four tries.

    :param int ndots: The number of dots which must be present in a domain name for it
        to be queried for "as is" prior to querying for it with the default domain
        extensions appended. The default value is 1 unless set otherwise by resolv.conf
        or the RES_OPTIONS environment variable.

    :param int tcp_port: The (TCP) port to use for queries. The default is 53.

    :param int udp_port: The (UDP) port to use for queries. The default is 53.

    :param list servers: List of nameservers to be used to do the lookups.

    :param list domains: The domains to search, instead of the domains specified
        in resolv.conf or the domain derived from the kernel hostname variable.

    :param str lookup: The lookups to perform for host queries. lookups should
        be set to a string of the characters "b" or "f", where "b" indicates a
        DNS lookup and "f" indicates a lookup in the hosts file.

    :param callable sock_state_cb: A callback function to be invoked when a
        socket changes state. Callback signature: ``sock_state_cb(self, fd, readable, writable)``

    The c-ares ``Channel`` provides asynchronous DNS operations.


    .. py:method:: gethostbyname(name, family, callback)

        :param string name: Name to query.

        :param int family: Socket family.

        :param callable callback: Callback to be called with the result of the query.

        Retrieves host information corresponding to a host name from a host database.

        Callback signature: ``callback(result, errorno)``


    .. py:method:: gethostbyaddr(name, callback)

        :param string name: Name to query.

        :param callable callback: Callback to be called with the result of the query.

        Retrieves the host information corresponding to a network address.

        Callback signature: ``callback(result, errorno)``


    .. py:method:: getnameinfo(name, port, flags, callback)

        :param string name: Name to query.

        :param int port: Port of the service to query.

        :param int flags: Query flags, see the NI flags section.

        :param callable callback: Callback to be called with the result of the query.

        Provides protocol-independent name resolution from an address to a host name and
        from a port number to the service name.

        Callback signature: ``callback(result, errorno)``


    .. py:method:: query(name, query_type, callback)

        :param string name: Name to query.

        :param int query_type: Type of query to perform.

        :param callable callback: Callback to be called with the result of the query.

        Do a DNS query of the specified type. Available types:
            - ``QUERY_TYPE_A``
            - ``QUERY_TYPE_AAAA``
            - ``QUERY_TYPE_CNAME``
            - ``QUERY_TYPE_MX``
            - ``QUERY_TYPE_NAPTR``
            - ``QUERY_TYPE_NS``
            - ``QUERY_TYPE_SOA``
            - ``QUERY_TYPE_SRV``
            - ``QUERY_TYPE_TXT``

        Callback signature: ``callback(result, errorno)``

    .. py:method:: cancel()

        Cancel any pending query on this channel. All pending callbacks will be called with ARES_ECANCELLED errorno.

    .. py:method:: destroy()

        Destroy the channel. All pending callbacks will be called with ARES_EDESTRUCTION errorno.

    .. py:method:: process_fd(read_fd, write_fd)

        :param int read_fd: File descriptor ready to read from.

        :param int write_fd: File descriptor ready to write to.

        Process the given file descriptors for read and/or write events.

    .. py:method:: getsock()

        Return a tuple containing 2 lists with the file descriptors ready to read and write.

    .. py:method:: timeout([max_timeout])

        :param float max_timeout: Maximum timeout.

        Determines the maximum time for which the caller should wait before invoking ``process_fd`` to process timeouts.
        If the ``max_timeout`` parameter is specified, it is stored on the channel and the appropriate value is then
        returned.

    .. py:method:: set_local_ip4(local_ip)

        :param str local_ip: IP address.

        Set the local IPv4 address from which the queries will be sent.

    .. py:method:: set_local_ip6(local_ip)

        :param str local_ip: IP address.

        Set the local IPv6 address from which the queries will be sent.

    .. py:method:: set_local_dev(local_dev)

        :param str local_dev: Network device name.

        Set the local ethernet device from which the queries will be sent.

    .. py:attribute:: servers

        List of nameservers to use for DNS queries.


