# coding=utf8

from distutils.core import setup, Extension
if os.name != 'posix' or sys.platform == 'darwin':
    from setup_cares import cares_build_ext
else:
    def cares_build_ext(build_ext):
        def build_extensions:
            return
import codecs

__version__ = "0.6.3"
libcares_version_required = '1.10.0'

def call(command):
  pipe = subprocess.Popen(command, shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
  pipe.wait()
  return pipe

def pkg_config_version_check(pkg, version):
  pipe = call('pkg-config --print-errors --exists "%s >= %s"' %
              (pkg, version))
  if pipe.returncode == 0:
    print '%s >= %s detected' % (pkg, version)
  else:
    print pipe.stderr.read()
    raise SystemExit('Error: %s >= %s not found' % (pkg, version))

def pkg_config_parse(opt, pkg):
  pipe = call("pkg-config %s %s" % (opt, pkg))
  output = pipe.stdout.read()
  opt = opt[-2:]
  return [x.lstrip(opt) for x in output.split()]

pkg_config_version_check ('libares', libares_version_required)
if sys.platform == 'win32':
  runtime_library_dirs = []
else:
  runtime_library_dirs = pkg_config_parse('--libs-only-L', 'libcares')

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
      cmdclass     = {'build_ext': cares_build_ext},
      ext_modules  = [Extension('pycares',
                                sources = ['src/pycares.c'],
                                define_macros=[('MODULE_VERSION', __version__)]
                                include_dirs = pkg_config_parse('--cflags-only-I', 'libcares'),
                                library_dirs = pkg_config_parse('--libs-only-L', 'libcares'),
                                libraries    = pkg_config_parse('--libs-only-l', 'libcares'),
                                runtime_library_dirs = runtime_library_dirs,
                     )]
     )

