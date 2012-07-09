
===================================
pycares: Python interface to c-ares
===================================

pycares is a Python module which provides an interface to c-ares.
c-ares (http://c-ares.haxx.se/) c-ares is a C library that performs
DNS requests and name resolves asynchronously.


Documentation
=============

http://readthedocs.org/docs/pycares/


Building
========

Linux:

::

    ./build_inplace

Mac OSX:

::

    (XCode needs to be installed)
    export CC="gcc -isysroot /Developer/SDKs/MacOSX10.6.sdk"
    export ARCHFLAGS="-arch x86_64"
    ./build_inplace

Microsoft Windows:

::

    (MinGW and MSYS need to be installed)
    ./build_inplace --compiler=mingw32


Running the test suite
======================

There are several ways of running the test ruite:

- Run the test with the current Python interpreter:

 From the toplevel directory, run: `nosetests -v -w tests/`

- Use Tox to run the test suite in several virtualenvs with several interpreters

 From the toplevel directory, run: `tox -e py26,py27,py32` this will run the test suite
 on Python 2.6, 2.7 and 3.2 (you'll need to have them installed beforehand)


Author
======

Saúl Ibarra Corretgé <saghul@gmail.com>


License
=======

Unless stated otherwise on-file pycares uses the MIT license, check LICENSE file.


Python versions
===============

Python >= 2.6 is supported. Yes, that includes Python 3 :-)


Contributing
============

If you'd like to contribute, fork the project, make a patch and send a pull
request. Have a look at the surrounding code and please, make yours look
alike :-)

