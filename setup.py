# coding=utf8

#USE DISTUTILS_DEBUG for debugging
#https://docs.python.org/2/distutils/extending.html
import logging as log
from setuptools import setup, Extension, Command
from distutils.errors import DistutilsOptionError
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

#run: setup.py build ext-static
#see: python setup.py --help-commands
class ext_static(Command):
    description = """Build the included libcares and link the Python module static [default: False]."""
    user_options = [('ext-static=', None, 'x')]
    boolean_options = ['ext-static']

    def initialize_options(self):
        self.ext_static = False

    def finalize_options(self):
        if self.ext_static not in (False, True):
            raise DistutilsOptionError('Specify True!')

    def run(self):
        if self.ext_static == True:
            log.debug('ext-static enabled!')
            global libcares_static
            libcares_static = True


def call(command, opt=None):
    pipe = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    pipe.wait()

    pipe.stdout = pipe.stdout.read()
    if pipe.stdout != None:
        if sys.version_info[0] >= 3:
            pipe.stdout = pipe.stdout.decode(sys.stdout.encoding) #get str
        pipe.stdout = pipe.stdout.split()
        if opt != None:
            pipe.stdout = [x.lstrip(opt) for x in pipe.stdout]
    pipe.stderr = pipe.stderr.read()
    if pipe.stderr != None:
        if sys.version_info[0] >= 3:
            pipe.stderr = pipe.stderr.decode(sys.stderr.encoding) #get str
        pipe.stderr = pipe.stderr.split()
    log.debug('%s - stdout: %s' % (command, pipe.stdout))
    log.debug('%s - stderr: %s' % (command, pipe.stderr))
    if pipe.returncode != 0:
        log.debug('%s - returncode: %i' % (command, pipe.returncode))
        raise SystemExit(pipe.stderr)
    else:
        return pipe


def pkg_config_version_check(pkg, version):
    try:
        pipe = call('pkg-config --print-errors --exists "%s >= %s"' %
                    (pkg, version))
    except:
        log.error(sys.exc_info()[0])
        raise SystemExit('Error: %s >= %s not found' % (pkg, version))

    log.debug('%s >= %s detected' % (pkg, version))

def pkg_config_parse(opt, pkg):
    pipe = call("pkg-config %s %s" % (opt, pkg), opt[-2:])
    if pipe.stdout != None:
        return pipe.stdout
    else:
        return []

if libcares_static == True:
    from setup_cares import cares_build_ext
    runtime_library_dirs = []
    include_dirs         = ['./deps/c-ares/src/']
    library_dirs         = []
    libraries            = []
    cmdclass             = {'build_ext': cares_build_ext,
            'ext-static': ext_static}
elif libcares_static == False:
    pkg_config_version_check('libcares', libcares_version_required)
    log.debug(pkg_config_parse('--libs-only-l',   'libcares'))
    runtime_library_dirs = pkg_config_parse('--libs-only-L',   'libcares')
    include_dirs         = pkg_config_parse('--cflags-only-I', 'libcares')
    library_dirs         = pkg_config_parse('--libs-only-L',   'libcares')
    libraries            = pkg_config_parse('--libs-only-l',   'libcares')
    cmdclass             = {'ext_static': ext_static}

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

