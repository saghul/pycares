
====================================
pycares: Python interface for c-ares
====================================

.. image:: https://badge.fury.io/py/pycares.png
    :target: http://badge.fury.io/py/pycares

.. image:: https://secure.travis-ci.org/saghul/pycares.png?branch=master
    :target: http://travis-ci.org/saghul/pycares

.. image:: https://ci.appveyor.com/api/projects/status/vx1wbkfq3l7nm1m8?svg=true
    :target: https://ci.appveyor.com/project/saghul/pycares

pycares is a Python module which provides an interface to c-ares.
`c-ares <http://c-ares.haxx.se>`_ is a C library that performs
DNS requests and name resolutions asynchronously.


Documentation
=============

http://readthedocs.org/docs/pycares/


Bundled c-ares
==============

pycares currently bundles c-ares and as of pycares 1.0.0 this is a strong requirement. Upstream
c-ares is not willing to apply `a patch adding TTL support <http://c-ares.haxx.se/mail/c-ares-archive-2013-07/0005.shtml>`_.
I did apply the patch to the bundled c-ares, but unfortunately it breaks the ABI, so attempting
to use a system provided c-ares is not possible.


Building
========

Linux:

::

    ./build_inplace

Mac OSX:

::

    (XCode needs to be installed)
    export ARCHFLAGS="-arch x86_64"
    ./build_inplace

Microsoft Windows (with Visual Studio 2008, 2010, 2015 or the Windows SDK):

::

    ./build_inplace


Running the test suite
======================

There are several ways of running the test ruite:

- Run the test with the current Python interpreter:

  From the toplevel directory, run: ``python tests/tests.py``

- Use Tox to run the test suite in several virtualenvs with several interpreters

  From the toplevel directory, run: ``tox -e py27,py33,py34,py35`` this will run the test suite
  on Python 2.7, 3.3, 3.4 and 3.5 (you'll need to have them installed beforehand)


Author
======

Saúl Ibarra Corretgé <saghul@gmail.com>


License
=======

Unless stated otherwise on-file pycares uses the MIT license, check LICENSE file.


Python versions
===============

Python >= 2.7 and >= 3.3 are supported. Other older versions might work too, but they are
not actively tested. Both CPython and PyPy (tested with version 5) are supported.


Contributing
============

If you'd like to contribute, fork the project, make a patch and send a pull
request. Have a look at the surrounding code and please, make yours look
alike :-)

