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

        This option is mutually exclusive with the ``event_thread`` option.

    :param bool event_thread: If set to True, c-ares will use its own thread
        to process events. This is the recommended way to use c-ares, as it
        allows for automatic reinitialization of the channel when the
        system resolver configuration changes.

        This option is mutually exclusive with the ``sock_state_cb`` option.

    :param int socket_send_buffer_size: Size for the created socket's send buffer.

    :param int socket_receive_buffer_size: Size for the created socket's receive buffer.

    :param bool rotate: If set to True, the nameservers are rotated when doing queries.

    :param str local_ip: Sets the local IP address for DNS operations.

    :param str local_dev: Sets the local network adapter to use for DNS operations. Linux only.

    :param str resolvconf_path: Path to resolv.conf, defaults to /etc/resolv.conf. Unix only.

    The c-ares ``Channel`` provides asynchronous DNS operations.

    The Channel object is designed to handle an unlimited number of DNS queries efficiently.
    Creating and destroying resolver instances repeatedly is resource-intensive and not
    recommended. Instead, create a single resolver instance and reuse it throughout your
    application's lifetime.

    .. important::
        It is recommended to explicitly close channels when done for predictable resource
        cleanup. Use :py:meth:`close` which can be called from any thread.
        While channels will attempt automatic cleanup during garbage collection, explicit
        closing is safer as it gives you control over when resources are released.


    .. py:method:: getaddrinfo(host, port, *, family=0, type=0, proto=0, flags=0, callback)

        :param string host: Hostname to resolve.

        :param string port: Service to resolve. Can be a string, int or None.

        :param callable callback: Callback to be called with the result of the query (keyword-only).

        The ``family``, ``type`` and ``proto`` arguments can be optionally specified in order to narrow the list of
        addresses returned. Passing zero as a value for each of these arguments selects the full range of results.
        The ``flags`` argument can be one or several of the ``AI_*`` constants, and will influence how results are
        computed and returned. For example, ``AI_NUMERICHOST`` will disable domain name resolution.

        Translate the host/port argument into a sequence of 5-tuples that contain all the necessary arguments for
        creating a socket connected to that service.

        Callback signature: ``callback(result, errorno)`` where result is an ``AddrInfoResult`` dataclass with:

            - ``cnames``: list of ``AddrInfoCname`` - CNAME records encountered
            - ``nodes``: list of ``AddrInfoNode`` - Address nodes

        Each ``AddrInfoCname`` is a dataclass with:

            - ``ttl``: int - Time to live in seconds
            - ``alias``: str - Alias name
            - ``name``: str - Canonical name

        Each ``AddrInfoNode`` is a dataclass with:

            - ``ttl``: int - Time to live in seconds
            - ``flags``: int - Address info flags
            - ``family``: int - Address family (socket.AF_INET or socket.AF_INET6)
            - ``socktype``: int - Socket type
            - ``protocol``: int - Protocol number
            - ``addr``: tuple - (ip, port) for IPv4 or (ip, port, flowinfo, scope_id) for IPv6


    .. py:method:: gethostbyaddr(name, *, callback)

        :param string name: Name to query.

        :param callable callback: Callback to be called with the result of the query (keyword-only).

        Retrieves the host information corresponding to a network address.

        Callback signature: ``callback(result, errorno)`` where result is a ``HostResult`` dataclass with:

            - ``name``: str - Canonical hostname
            - ``aliases``: list[str] - List of hostname aliases
            - ``addresses``: list[str] - List of IP addresses


    .. py:method:: getnameinfo(address, flags, *, callback)

        :param tuple address: address tuple to get info about.

        :param int flags: Query flags, see the NI flags section.

        :param callable callback: Callback to be called with the result of the query (keyword-only).

        Provides protocol-independent name resolution from an address to a host name and
        from a port number to the service name.

        ``address`` must be a 2-item tuple for IPv4 or a 4-item tuple for IPv6. Format of
        fields is the same as one returned by `getaddrinfo()`.

        Callback signature: ``callback(result, errorno)`` where result is a ``NameInfoResult`` dataclass with:

            - ``node``: str - Hostname or IP address information
            - ``service``: str | None - Service name or port information


    .. py:method:: query(name, query_type, *, query_class=QUERY_CLASS_IN, callback)

        :param string name: Name to query.

        :param int query_type: Type of query to perform.

        :param callable callback: Callback to be called with the result of the query (keyword-only).

        :param int query_class: Query class (default: QUERY_CLASS_IN).

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

        Callback signature: ``callback(result, errorno)`` where result is a ``DNSResult`` dataclass with:

            - ``answer``: list of ``DNSRecord`` - Records from the answer section
            - ``authority``: list of ``DNSRecord`` - Records from the authority section
            - ``additional``: list of ``DNSRecord`` - Records from the additional section

        Each ``DNSRecord`` is a dataclass with:

            - ``name``: str - Domain name
            - ``type``: int - Record type constant
            - ``record_class``: int - Record class constant
            - ``ttl``: int - Time to live in seconds (real TTL values from DNS server)
            - ``data``: Record-specific dataclass (see below)

        **Record data types by query type:**

            - **A**: ``ARecordData`` dataclass

              - ``addr``: str - IPv4 address

            - **AAAA**: ``AAAARecordData`` dataclass

              - ``addr``: str - IPv6 address

            - **CAA**: ``CAARecordData`` dataclass

              - ``critical``: int - Critical flag
              - ``tag``: str - Property tag
              - ``value``: str - Property value

            - **CNAME**: ``CNAMERecordData`` dataclass

              - ``cname``: str - Canonical name

            - **MX**: ``MXRecordData`` dataclass

              - ``priority``: int - Mail server priority
              - ``exchange``: str - Mail server hostname

            - **NAPTR**: ``NAPTRRecordData`` dataclass

              - ``order``: int - Order value
              - ``preference``: int - Preference value
              - ``flags``: str - Flags string
              - ``service``: str - Service string
              - ``regexp``: str - Regular expression
              - ``replacement``: str - Replacement string

            - **NS**: ``NSRecordData`` dataclass

              - ``nsdname``: str - Name server domain name

            - **PTR**: ``PTRRecordData`` dataclass

              - ``dname``: str - Domain name pointer

            - **SOA**: ``SOARecordData`` dataclass

              - ``mname``: str - Primary name server
              - ``rname``: str - Responsible party email
              - ``serial``: int - Serial number
              - ``refresh``: int - Refresh interval
              - ``retry``: int - Retry interval
              - ``expire``: int - Expire time
              - ``minimum``: int - Minimum TTL

            - **SRV**: ``SRVRecordData`` dataclass

              - ``priority``: int - Priority
              - ``weight``: int - Weight
              - ``port``: int - Port number
              - ``target``: str - Target hostname

            - **TXT**: ``TXTRecordData`` dataclass

              - ``text``: str - Text content

        **Example:**

        .. code-block:: python

            def callback(result, error):
                if error:
                    print(f"Error: {error}")
                    return

                print(f"Answer section: {len(result.answer)} records")
                for record in result.answer:
                    print(f"  {record.name} TTL={record.ttl}s: {record.data}")

                if result.authority:
                    print(f"Authority section: {len(result.authority)} records")

                if result.additional:
                    print(f"Additional section: {len(result.additional)} records")

            channel.query("google.com", pycares.QUERY_TYPE_A, callback=callback)

    .. py:method:: search(name, query_type, *, query_class=QUERY_CLASS_IN, callback)

        :param string name: Name to query.

        :param int query_type: Type of query to perform.

        :param callable callback: Callback to be called with the result of the query (keyword-only).

        :param int query_class: Query class (default: QUERY_CLASS_IN).

        This function does the same as :py:meth:`query` but it will honor the ``domain`` and ``search`` directives in
        ``resolv.conf``. The callback signature and return types are identical to :py:meth:`query`.

    .. py:method:: cancel()

        Cancel any pending query on this channel. All pending callbacks will be called with ARES_ECANCELLED errorno.

    .. py:method:: close()

        Close the channel as soon as it's safe to do so.

        This method can be called from any thread. The channel will be destroyed
        safely using a background thread with a 1-second delay to ensure c-ares
        has completed its cleanup.

        Once close() is called, no new queries can be started. Any pending
        queries will be cancelled and their callbacks will receive ARES_ECANCELLED.

        .. note::
            It is recommended to explicitly call :py:meth:`close` rather than
            relying on garbage collection. Explicit closing provides:

            - Control over when resources are released
            - Predictable shutdown timing
            - Proper cleanup of all resources

            While the channel will attempt cleanup during garbage collection,
            explicit closing is safer and more predictable.

        .. versionadded:: 4.9.0

    .. py:method:: wait(timeout=None)

        :param float timeout: Maximum time to wait for events. If None, wait indefinitely.

        Waits for pending queries to be completed.

        Returns `True` if all queries completed, `False` if the timeout was reached.

        .. versionadded:: 5.0.0

    .. py:method:: reinit()

        Reinitialize the channel.

        For more details, see the `ares_reinit documentation <https://c-ares.org/docs/ares_reinit.html>`_.

    .. py:method:: process_fd(read_fd, write_fd)

        :param int read_fd: File descriptor ready to read from.

        :param int write_fd: File descriptor ready to write to.

        Process the given file descriptors for read and/or write events.

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
