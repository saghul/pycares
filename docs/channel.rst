.. _channel:


.. currentmodule:: pycares


====================================
:py:class:`Channel`  -  Ares Channel
====================================


.. py:class:: Channel([flags, timeout, tries, ndots, tcp_port, udp_port, servers, domains, lookups, sock_state_cb, socket_send_buffer_size, socket_receive_buffer_size, rotate, local_ip, local_dev, resolvconf_path])

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

    :param int socket_send_buffer_size: Size for the created socket's send buffer.

    :param int socket_receive_buffer_size: Size for the created socket's receive buffer.

    :param bool rotate: If set to True, the nameservers are rotated when doing queries.

    :param str local_ip: Sets the local IP address for DNS operations.

    :param str local_dev: Sets the local network adapter to use for DNS operations. Linux only.

    :param str resolvconf_path: Path to resolv.conf, defaults to /etc/resolv.conf. Unix only.

    The c-ares ``Channel`` provides asynchronous DNS operations.

    .. py:method:: getaddrinfo(host, port, callback, family=0, type=0, proto=0, flags=0)

        :param string host: Hostname to resolve.

        :param string port: Service to resolve. Can be a string, int or None.

        :param callable callback: Callback to be called with the result of the query.

        The ``family``, ``type`` and ``proto`` arguments can be optionally specified in order to narrow the list of
        addresses returned. Passing zero as a value for each of these arguments selects the full range of results.
        The ``flags`` argument can be one or several of the ``AI_*`` constants, and will influence how results are
        computed and returned. For example, ``AI_NUMERICHOST`` will disable domain name resolution.

        Translate the host/port argument into a sequence of 5-tuples that contain all the necessary arguments for
        creating a socket connected to that service.

        Callback signature: ``callback(result, errorno)``


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


    .. py:method:: getnameinfo(address, flags, callback)

        :param tuple address: address tuple to get info about.

        :param int flags: Query flags, see the NI flags section.

        :param callable callback: Callback to be called with the result of the query.

        Provides protocol-independent name resolution from an address to a host name and
        from a port number to the service name.

        ``address`` must be a 2-item tuple for IPv4 or a 4-item tuple for IPv6. Format of
        fields is the same as one returned by `getaddrinfo()`.

        Callback signature: ``callback(result, errorno)``


    .. py:method:: query(name, query_type, callback)

        :param string name: Name to query.

        :param int query_type: Type of query to perform.

        :param callable callback: Callback to be called with the result of the query.

        Do a DNS query of the specified type. Available types:
            - ``QUERY_TYPE_A``
            - ``QUERY_TYPE_AAAA``
            - ``QUERY_TYPE_ANY``
            - ``QUERY_TYPE_CAA``
            - ``QUERY_TYPE_CNAME``
            - ``QUERY_TYPE_MX``
            - ``QUERY_TYPE_NAPTR``
            - ``QUERY_TYPE_NS``
            - ``QUERY_TYPE_PTR``
            - ``QUERY_TYPE_SOA``
            - ``QUERY_TYPE_SRV``
            - ``QUERY_TYPE_TXT``

        Callback signature: ``callback(result, errorno)``. The result type varies depending on the
        query type:

            - A: (list of) ``ares_query_a_result``, fields:

              - host
              - ttl

            - AAAA: (list of) ``ares_query_aaaa_result``, fields:

              - host
              - ttl

            - CAA: (list of) ``ares_query_caa_result``, fields:

              - critical
              - property
              - value
              - ttl

            - CNAME: ``ares_query_cname_result``, fields:

              - cname
              - ttl

            - MX: (list of) ``ares_query_mx_result``, fields:

              - host
              - priority
              - ttl

            - NAPTR: (list of) ``ares_query_naptr_result``, fields:

              - order
              - preference
              - flags
              - service
              - regex
              - replacement
              - ttl

            - NS: (list of) ``ares_query_ns_result``, fields:

              - host
              - ttl

            - PTR: (list of) ``ares_query_ptr_result``, fields:

              - name
              - ttl

            - SOA: ``ares_query_soa_result``, fields:

              - nsname
              - hostmaster
              - serial
              - refresh
              - retry
              - expires
              - minttl
              - ttl

            - SRV: (list of) ``ares_query_srv_result``, fields:

              - host
              - port
              - priority
              - weight
              - ttl

            - TXT: (list of) ``ares_query_txt_result``, fields:

              - text
              - ttl

            - ANY: a list of any of the above.

        .. note::
            TTL is not implemented for CNAME and NS), so it's set to -1.

    .. py:method:: search(name, query_type, callback)

        :param string name: Name to query.

        :param int query_type: Type of query to perform.

        :param callable callback: Callback to be called with the result of the query.

        Tis function does the same as :py:meth:`query` but it will honor the ``domain`` and ``search`` directives in
        ``resolv.conf``.

    .. py:method:: cancel()

        Cancel any pending query on this channel. All pending callbacks will be called with ARES_ECANCELLED errorno.

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

    .. py:method:: set_local_ip(local_ip)

        :param str local_ip: IP address.

        Set the local IPv4 or IPv6 address from which the queries will be sent.

    .. py:method:: set_local_dev(local_dev)

        :param str local_dev: Network device name.

        Set the local ethernet device from which the queries will be sent.

    .. py:attribute:: servers

        List of nameservers to use for DNS queries.

