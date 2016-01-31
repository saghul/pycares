#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, Extension
from setup_cares import cares_build_ext
import codecs

__version__ = "1.0.0"

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
      ],
      cmdclass     = {'build_ext': cares_build_ext},
      ext_modules  = [Extension('pycares',
                                sources = ['src/pycares.c'],
                                define_macros=[('MODULE_VERSION', __version__)]
                     )]
     )

