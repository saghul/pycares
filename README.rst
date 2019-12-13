pycares: Python interface for c-ares
====================================

.. image:: https://badge.fury.io/py/pycares.png
    :target: http://badge.fury.io/py/pycares

.. image:: https://secure.travis-ci.org/saghul/pycares.png?branch=master
    :target: http://travis-ci.org/saghul/pycares

.. image:: https://ci.appveyor.com/api/projects/status/vx1wbkfq3l7nm1m8?svg=true
    :target: https://ci.appveyor.com/project/saghul/pycares

.. image:: https://github.com/saghul/pycares/workflows/Test%20macOS/badge.svg
    :target: https://github.com/saghul/pycares/actions)

pycares is a Python module which provides an interface to c-ares.
`c-ares <http://c-ares.haxx.se>`_ is a C library that performs
DNS requests and name resolutions asynchronously.


Documentation
-------------

http://readthedocs.org/docs/pycares/


Bundled c-ares
--------------

pycares currently bundles c-ares and as of pycares 1.0.0 this is a strong requirement. Upstream
c-ares is not willing to apply `a patch adding TTL support <http://c-ares.haxx.se/mail/c-ares-archive-2013-07/0005.shtml>`_.
I did apply the patch to the bundled c-ares, but unfortunately it breaks the ABI, so attempting
to use a system provided c-ares is not possible.


Installation
------------

GNU/Linux, macOS, Windows, others:

::

    pip install pycares

FreeBSD:

::

    cd /usr/ports/dns/py-pycares && make install


IDNA 2008 support
^^^^^^^^^^^^^^^^^

If the ``idna`` package is installed, pycares will support IDNA 2008 encodingm otherwise the builtin idna codec will be used,
which provides IDNA 2003 support.

You can force this at installation time as follows:

::

   pip install pycares[idna]


Running the test suite
----------------------

There are several ways of running the test ruite:

- Run the test with the current Python interpreter:

  From the toplevel directory, run: ``python tests/tests.py``

- Use Tox to run the test suite in several virtualenvs with several interpreters

  From the toplevel directory, run: ``tox -e py35,py36,py37`` this will run the test suite
  on Python 3.5, 3.6 and 3.7 (you'll need to have them installed beforehand)


Using it from the cli, a la dig
-------------------------------

This module can be used directly from the command line in a similar fashion to dig (limited, of course):

::

   $ python -m pycares google.com
   ;; QUESTION SECTION:
   ;google.com			IN	A

   ;; ANSWER SECTION:
   google.com		300	IN	A	172.217.17.142

   $ python -m pycares mx google.com
   ;; QUESTION SECTION:
   ;google.com			IN	MX

   ;; ANSWER SECTION:
   google.com		600	IN	MX	50 alt4.aspmx.l.google.com
   google.com		600	IN	MX	10 aspmx.l.google.com
   google.com		600	IN	MX	40 alt3.aspmx.l.google.com
   google.com		600	IN	MX	20 alt1.aspmx.l.google.com
   google.com		600	IN	MX	30 alt2.aspmx.l.google.com


Author
------

Saúl Ibarra Corretgé <s@saghul.net>


License
-------

Unless stated otherwise on-file pycares uses the MIT license, check LICENSE file.


Supported Python versions
-------------------------

Python >= 3.5 are supported. Both CPython and PyPy are supported.


Contributing
------------

If you'd like to contribute, fork the project, make a patch and send a pull
request. Have a look at the surrounding code and please, make yours look
alike :-)
