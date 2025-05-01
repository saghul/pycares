.. _pycares:


*************************************************
:py:mod:`pycares` --- Python interface to c-ares.
*************************************************

.. py:module:: pycares
    :platform: POSIX, Windows
    :synopsis: Python interface to c-ares.

.. seealso::
    `c-ares source code
    <http://github.com/bagder/c-ares>`_.

ares_threadsafety
=================

.. py:function:: ares_threadsafety()

    Check if c-ares was compiled with thread safety support.

    :returns: True if thread-safe, False otherwise.
    :rtype: bool


Objects
*******

.. toctree::
    :maxdepth: 2
    :titlesonly:

    channel
    constants
    errno
    event_loops

