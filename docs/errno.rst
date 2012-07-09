.. _errno:


.. currentmodule:: pycares


======================================================
:py:mod:`pycares.errno` --- Error constant definitions
======================================================


This module contains the defined error constants from c-ares.

.. py:attribute:: pycares.errno.errorcode

    Mapping (code, string) with c-ares error codes.

.. py:function:: pycares.errno.strerror(errorno)

    :param int errorno: Error number.

    Get the string representation of the given c-ares error number.

