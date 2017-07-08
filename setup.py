#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import platform
import re

from setuptools import setup, Extension
from setup_cares import cares_build_ext


kwargs = {}
packages = ['pycares']
if (platform.python_implementation() == 'PyPy' or os.environ.get('PYCARES_CFFI', '0') != '0'):
    # cffi module
    kwargs['setup_requires'] = ['cffi>=1.5.0']
    kwargs['install_requires'] = ['cffi>=1.5.0']
    kwargs['cffi_modules'] = ['pycares/_cfficore/pycares_build.py:ffi']
    packages.append('pycares._cfficore')
else:
    kwargs['ext_modules'] = [Extension('pycares._core', sources = ['src/pycares.c'])]
kwargs['packages'] = packages


def get_version():
    return re.search(r"""__version__\s+=\s+(?P<quote>['"])(?P<version>.+?)(?P=quote)""", open('pycares/_version.py').read()).group('version')


setup(name             = 'pycares',
      version          = get_version(),
      author           = 'Saúl Ibarra Corretgé',
      author_email     = 'saghul@gmail.com',
      url              = 'http://github.com/saghul/pycares',
      description      = 'Python interface for c-ares',
      long_description = codecs.open('README.rst', encoding='utf-8').read(),
      platforms        = ['POSIX', 'Microsoft Windows'],
      classifiers      = [
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
      ],
      cmdclass     = {'build_ext': cares_build_ext},
      **kwargs
)
