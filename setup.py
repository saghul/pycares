#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re
import sys

# we have to import setup_cares.py which is in project's root folder
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from setuptools import setup

from setup_cares import cares_build_ext


def get_version():
    return re.search(r"""__version__\s+=\s+(?P<quote>['"])(?P<version>.+?)(?P=quote)""", open('src/pycares/_version.py').read()).group('version')


setup(name             = 'pycares',
      version          = get_version(),
      author           = 'Saúl Ibarra Corretgé',
      author_email     = 's@saghul.net',
      license          = 'MIT',
      url              = 'http://github.com/saghul/pycares',
      description      = 'Python interface for c-ares',
      long_description = codecs.open('PYPIREADME.rst', encoding='utf-8').read(),
      long_description_content_type = 'text/x-rst',
      platforms        = ['POSIX', 'Microsoft Windows'],
      classifiers      = [
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Programming Language :: Python :: 3.13',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
      ],
      cmdclass         = {'build_ext': cares_build_ext},
      install_requires = ['cffi>=1.5.0'],
      extras_require   = {'idna': ['idna >= 2.1']},
      python_requires  = '>=3.9',
      cffi_modules     = ['src/_cffi_src/build_cares.py:ffi'],
      package_dir      = {'': 'src'},
      packages         = ['pycares'],
      ext_package      = 'pycares',
      zip_safe         = False
)
