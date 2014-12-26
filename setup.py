# coding=utf8

from __future__ import print_function
#https://docs.python.org/2/distutils/extending.html
from distutils.command.build_py import build_py as _build_py_static
from distutils.core import setup, Extension
import codecs
import sys
import os
import io
try:
    import subprocess32 as subprocess #backported python3 subprocess in python2
except:
    import subprocess

__version__ = "0.6.3"
libcares_version_required = '1.10.0'
libcares_static = False

class build_py_static(_build_py_static):
    """Build the Python source with included libcares and link static."""
    libcares_static = True

def call(command):
    pipe = subprocess.call(command, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    pipe.wait()
    return pipe


def pkg_config_version_check(pkg, version):
    pipe = call('pkg-config --print-errors --exists "%s >= %s"' %
                (pkg, version))
    if pipe.returncode == 0:
        print('%s >= %s detected' % (pkg, version))
    else:
        print(pipe.stderr.read())
        raise SystemExit('Error: %s >= %s not found' % (pkg, version))


def pkg_config_parse(opt, pkg):
    pipe = call("pkg-config %s %s" % (opt, pkg))
    output = pipe.stdout.read()
    opt = opt[-2:]
    return [x.decode(sys.stdout.encoding).lstrip(opt) for x in output.split()]

if libcares_static == True:
    from setup_cares import cares_build_ext
    runtime_library_dirs = []
    include_dirs         = ['./deps/c-ares/src/']
    library_dirs         = []
    libraries            = []
    cmdclass             = {'build_ext': cares_build_ext}
else if libcares_static == False:
    pkg_config_version_check('libcares', libcares_version_required)
    print(pkg_config_parse('--libs-only-l',   'libcares'))
    runtime_library_dirs = pkg_config_parse('--libs-only-L',   'libcares')
    include_dirs         = pkg_config_parse('--cflags-only-I', 'libcares')
    library_dirs         = pkg_config_parse('--libs-only-L',   'libcares')
    libraries            = pkg_config_parse('--libs-only-l',   'libcares')
    cmdclass             = {}

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
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.0",
          "Programming Language :: Python :: 3.1",
          "Programming Language :: Python :: 3.2",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4"
      ],
      cmdclass     = cmdclass,
      ext_modules  = [Extension('pycares',
                                sources = ['src/pycares.c'],
                                define_macros=[('MODULE_VERSION', __version__)],
                                include_dirs = include_dirs,
                                library_dirs = library_dirs,
                                libraries    = libraries,
                                runtime_library_dirs = runtime_library_dirs,
                     )]
     )

