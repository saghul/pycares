#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, Extension, find_packages
from setup_cares import cares_build_ext
import codecs
import platform 
import os

__version__ = "1.0.0"
kwargs = {}
packages = ["pycares",]

if (platform.python_implementation() == 'PyPy' or
        os.environ.get('PYCARES_CFFI', '0') != '0'):
    # cffi module
    kwargs['setup_requires'] = ["cffi>=1.5.0"]
    kwargs['install_requires'] = ["cffi>=1.5.0"]
    kwargs['cffi_modules'] = ["pycares/_cfficore/pycares_build.py:ffi"]
    packages.append("pycares._cfficore")
else:
    kwargs['ext_modules'] = [Extension('pycares._core',
                                       sources = ['src/pycares.c'],
                                       define_macros=[('MODULE_VERSION', __version__)]
                                      )]

kwargs['packages'] = packages


setup(name             = "pycares",
      version          = __version__,
      author           = "Saúl Ibarra Corretgé",
      author_email     = "saghul@gmail.com",
      url              = "http://github.com/saghul/pycares",
      description      = "Python interface for c-ares",
      long_description = codecs.open("README.rst", encoding="utf-8").read(),
      platforms        = ["POSIX", "Microsoft Windows"],
      classifiers      = [
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: POSIX",
          "Operating System :: Microsoft :: Windows",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4"
          "Programming Language :: Python :: 3.5"
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
      ],
      cmdclass     = {'build_ext': cares_build_ext},
      **kwargs
     )

