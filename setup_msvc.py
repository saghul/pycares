# coding=utf8

from distutils.core import setup, Extension

__version__ = "0.3.0"

setup(name             = "pycares",
      version          = __version__,
      author           = "Saúl Ibarra Corretgé",
      author_email     = "saghul@gmail.com",
      url              = "http://github.com/saghul/pycares",
      description      = "Python interface for c-ares",
      long_description = open("README.rst").read(),
      platforms        = ["POSIX", "Microsoft Windows"],
      classifiers      = [
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: POSIX",
          "Operating System :: Microsoft :: Windows",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.0",
          "Programming Language :: Python :: 3.1",
          "Programming Language :: Python :: 3.2"
      ],
      ext_modules  = [
          Extension('pycares',
              sources = ['src/pycares.c'],
	      extra_objects = ['deps/c-ares/libcares.lib', 'ws2_32.lib', 'advapi32.lib'],
	      include_dirs = ['deps/c-ares/src'],
              define_macros=[('MODULE_VERSION', __version__)]
          )]
     )

