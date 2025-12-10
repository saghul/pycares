.. _migration:

*******************************
Migrating to pycares 5.0
*******************************

pycares 5.0 is a major release with significant API changes. This guide
covers all breaking changes and how to update your code.

Breaking Changes
================

DNS Query Results API
---------------------

The DNS query API has been completely rewritten. Query results now use
structured dataclasses instead of the previous format.

**Before (4.x):**

.. code-block:: python

    def callback(result, error):
        if error:
            print(f"Error: {error}")
            return
        # result was a list of record-specific objects
        for record in result:
            print(record.host)  # A record example

    channel.query("example.com", pycares.QUERY_TYPE_A, callback)

**After (5.0):**

.. code-block:: python

    def callback(result, error):
        if error:
            print(f"Error: {error}")
            return
        # result is now a DNSResult with answer/authority/additional sections
        for record in result.answer:
            print(f"{record.name} TTL={record.ttl}: {record.data.addr}")

    channel.query("example.com", pycares.QUERY_TYPE_A, callback=callback)

The new :class:`DNSResult` dataclass contains three sections:

- ``answer``: List of answer records (the main query results)
- ``authority``: List of authority records (nameserver information)
- ``additional``: List of additional records

Each record is a :class:`DNSRecord` dataclass with:

- ``name``: Domain name (str)
- ``type``: Record type constant (int)
- ``record_class``: Record class, typically ``QUERY_CLASS_IN`` (int)
- ``ttl``: Time to live in seconds (int)
- ``data``: Type-specific dataclass with the record content

Record data types:

- :class:`ARecordData`: ``addr`` (IPv4 address)
- :class:`AAAARecordData`: ``addr`` (IPv6 address)
- :class:`MXRecordData`: ``priority``, ``exchange``
- :class:`TXTRecordData`: ``data`` (bytes)
- :class:`CAARecordData`: ``critical``, ``tag``, ``value``
- :class:`CNAMERecordData`: ``cname``
- :class:`NAPTRRecordData`: ``order``, ``preference``, ``flags``, ``service``, ``regexp``, ``replacement``
- :class:`NSRecordData`: ``nsdname``
- :class:`PTRRecordData`: ``dname``
- :class:`SOARecordData`: ``mname``, ``rname``, ``serial``, ``refresh``, ``retry``, ``expire``, ``minimum``
- :class:`SRVRecordData`: ``priority``, ``weight``, ``port``, ``target``
- :class:`TLSARecordData`: ``cert_usage``, ``selector``, ``matching_type``, ``cert_association_data``
- :class:`HTTPSRecordData`: ``priority``, ``target``, ``params``
- :class:`URIRecordData`: ``priority``, ``weight``, ``target``


Channel Constructor Arguments Are Keyword-Only
----------------------------------------------

All :class:`Channel` constructor arguments must now be passed as keyword arguments.

**Before (4.x):**

.. code-block:: python

    # Positional arguments worked
    channel = pycares.Channel(0, 5.0, 4, 1)

**After (5.0):**

.. code-block:: python

    # All arguments must be keyword arguments
    channel = pycares.Channel(flags=0, timeout=5.0, tries=4, ndots=1)


event_thread Parameter Removed
------------------------------

The ``event_thread`` parameter has been removed from the :class:`Channel`
constructor. Event thread mode is now implicit:

- If ``sock_state_cb`` is **not** provided: event thread mode is automatically enabled
- If ``sock_state_cb`` **is** provided: manual event loop integration is assumed

**Before (4.x):**

.. code-block:: python

    # Explicit event thread mode
    channel = pycares.Channel(event_thread=True)

    # Or with sock_state_cb for manual mode
    channel = pycares.Channel(sock_state_cb=my_callback, event_thread=False)

**After (5.0):**

.. code-block:: python

    # Event thread mode (automatic when no sock_state_cb)
    channel = pycares.Channel()

    # Manual event loop integration
    channel = pycares.Channel(sock_state_cb=my_callback)


callback Parameter Is Mandatory and Keyword-Only
------------------------------------------------

The ``callback`` parameter for query methods must now be explicitly provided
as a keyword argument.

**Before (4.x):**

.. code-block:: python

    channel.query("example.com", pycares.QUERY_TYPE_A, my_callback)

**After (5.0):**

.. code-block:: python

    channel.query("example.com", pycares.QUERY_TYPE_A, callback=my_callback)


Removed Functions
-----------------

gethostbyname()
^^^^^^^^^^^^^^^

The ``gethostbyname()`` method has been removed. Use ``getaddrinfo()`` instead.

**Before (4.x):**

.. code-block:: python

    channel.gethostbyname("example.com", socket.AF_INET, callback)

**After (5.0):**

.. code-block:: python

    channel.getaddrinfo(
        host="example.com",
        port=None,
        family=socket.AF_INET,
        callback=callback
    )

getsock()
^^^^^^^^^

The ``getsock()`` method has been removed. Use ``sock_state_cb`` for event
loop integration or rely on the automatic event thread mode.

**Before (4.x):**

.. code-block:: python

    read_fds, write_fds = channel.getsock()
    # Manual polling of file descriptors

**After (5.0):**

.. code-block:: python

    def sock_state_cb(fd, readable, writable):
        # Register/unregister fd with your event loop
        pass

    channel = pycares.Channel(sock_state_cb=sock_state_cb)

Or simply use event thread mode by not providing ``sock_state_cb``.


TXT Records Return Bytes
------------------------

TXT record data is now returned as ``bytes`` instead of ``str``.

**Before (4.x):**

.. code-block:: python

    for record in result:
        print(record.text)  # str

**After (5.0):**

.. code-block:: python

    for record in result.answer:
        print(record.data.data)  # bytes
        print(record.data.data.decode())  # decode if needed


New Features
============

New Query Types
---------------

pycares 5.0 adds support for new DNS record types:

- ``QUERY_TYPE_TLSA``: DANE TLSA records for certificate association
- ``QUERY_TYPE_HTTPS``: HTTPS service binding records
- ``QUERY_TYPE_URI``: URI records

.. code-block:: python

    channel.query("_443._tcp.example.com", pycares.QUERY_TYPE_TLSA, callback=callback)
    channel.query("example.com", pycares.QUERY_TYPE_HTTPS, callback=callback)
    channel.query("example.com", pycares.QUERY_TYPE_URI, callback=callback)


Channel.wait() Method
---------------------

A new ``wait()`` method allows waiting for all pending queries to complete:

.. code-block:: python

    channel = pycares.Channel()
    channel.query("example.com", pycares.QUERY_TYPE_A, callback=callback)
    channel.query("example.com", pycares.QUERY_TYPE_AAAA, callback=callback)

    # Wait for all queries to complete (with optional timeout in seconds)
    channel.wait(timeout=10.0)


Build System Changes
====================

CMake Required
--------------

pycares now uses CMake to build the bundled c-ares library. Ensure CMake >= 3.5
is installed:

- Ubuntu/Debian: ``apt-get install cmake``
- macOS: ``brew install cmake``
- Windows: Download from https://cmake.org/download/

Thread Safety Mandatory
-----------------------

c-ares is now always built with thread safety enabled. This is required for
the implicit event thread mode and ensures safe operation in multi-threaded
applications.


Quick Migration Checklist
=========================

1. Update all query callbacks to handle the new ``DNSResult`` dataclass format
2. Change all ``Channel()`` calls to use keyword arguments
3. Remove any ``event_thread=True/False`` parameters
4. Add ``callback=`` keyword to all query/search method calls
5. Replace ``gethostbyname()`` with ``getaddrinfo()``
6. Remove ``getsock()`` usage; use ``sock_state_cb`` or event thread mode
7. Update TXT record handling to expect ``bytes`` instead of ``str``
8. Ensure CMake >= 3.5 is installed for building from source
