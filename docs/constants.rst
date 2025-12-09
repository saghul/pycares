.. _constants:

========================
c-ares library constants
========================


Channel flags
=============

.. py:data:: pycares.ARES_FLAG_USEVC
.. py:data:: pycares.ARES_FLAG_PRIMARY
.. py:data:: pycares.ARES_FLAG_IGNTC
.. py:data:: pycares.ARES_FLAG_NORECURSE
.. py:data:: pycares.ARES_FLAG_STAYOPEN
.. py:data:: pycares.ARES_FLAG_NOSEARCH
.. py:data:: pycares.ARES_FLAG_NOALIASES
.. py:data:: pycares.ARES_FLAG_NOCHECKRESP

.. seealso::
    `c-ares documentation for ares_init <https://c-ares.org/ares_init.html>`_


Nameinfo constants
==================

.. py:data:: pycares.ARES_NI_NOFQDN
.. py:data:: pycares.ARES_NI_NUMERICHOST
.. py:data:: pycares.ARES_NI_NAMEREQD
.. py:data:: pycares.ARES_NI_NUMERICSERV
.. py:data:: pycares.ARES_NI_DGRAM
.. py:data:: pycares.ARES_NI_TCP
.. py:data:: pycares.ARES_NI_UDP
.. py:data:: pycares.ARES_NI_SCTP
.. py:data:: pycares.ARES_NI_DCCP
.. py:data:: pycares.ARES_NI_NUMERICSCOPE
.. py:data:: pycares.ARES_NI_LOOKUPHOST
.. py:data:: pycares.ARES_NI_LOOKUPSERVICE
.. py:data:: pycares.ARES_NI_IDN
.. py:data:: pycares.ARES_NI_IDN_ALLOW_UNASSIGNED
.. py:data:: pycares.ARES_NI_IDN_USE_STD3_ASCII_RULES

.. seealso::
    `c-ares documentation for ares_getnameinfo <https://c-ares.org/ares_getnameinfo.html>`_

Query types
===========

.. py:data:: pycares.QUERY_TYPE_A

    IPv4 address record.

.. py:data:: pycares.QUERY_TYPE_AAAA

    IPv6 address record.

.. py:data:: pycares.QUERY_TYPE_ANY

    Any record type (may be restricted by some DNS servers).

.. py:data:: pycares.QUERY_TYPE_CAA

    Certification Authority Authorization record.

.. py:data:: pycares.QUERY_TYPE_CNAME

    Canonical name record.

.. py:data:: pycares.QUERY_TYPE_HTTPS

    HTTPS service binding record (RFC 9460). Used for discovering HTTPS
    endpoints and their parameters like supported protocols (h2, h3),
    alternative ports, and IP hints.

.. py:data:: pycares.QUERY_TYPE_MX

    Mail exchange record.

.. py:data:: pycares.QUERY_TYPE_NAPTR

    Naming Authority Pointer record.

.. py:data:: pycares.QUERY_TYPE_NS

    Name server record.

.. py:data:: pycares.QUERY_TYPE_PTR

    Pointer record (reverse DNS lookup).

.. py:data:: pycares.QUERY_TYPE_SOA

    Start of Authority record.

.. py:data:: pycares.QUERY_TYPE_SRV

    Service locator record.

.. py:data:: pycares.QUERY_TYPE_TLSA

    TLSA record for DANE TLS authentication (RFC 6698). Used to associate
    TLS server certificates or public keys with domain names, enabling
    certificate pinning via DNS.

.. py:data:: pycares.QUERY_TYPE_TXT

    Text record.

.. py:data:: pycares.QUERY_TYPE_URI

    URI record (RFC 7553). Used for publishing mappings from hostnames
    to URIs.


Query classes
=============

.. py:data:: pycares.QUERY_CLASS_IN

    Internet class (default).

.. py:data:: pycares.QUERY_CLASS_CHAOS

    Chaos class.

.. py:data:: pycares.QUERY_CLASS_HESOID

    Hesoid class.

.. py:data:: pycares.QUERY_CLASS_NONE

    None class.

.. py:data:: pycares.QUERY_CLASS_ANY

    Any class.


Others
======

.. py:data:: pycares.ARES_SOCKET_BAD


