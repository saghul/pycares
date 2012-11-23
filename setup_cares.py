
import os
import subprocess
import sys

from distutils import log
from distutils.command.build_ext import build_ext
from distutils.errors import DistutilsError


def exec_process(cmdline, silent=True, input=None, **kwargs):
    """Execute a subprocess and returns the returncode, stdout buffer and stderr buffer.
    Optionally prints stdout and stderr while running."""
    try:
        sub = subprocess.Popen(args=cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        stdout, stderr = sub.communicate(input=input)
        returncode = sub.returncode
        if not silent:
            sys.stdout.write(stdout)
            sys.stderr.write(stderr)
    except OSError as e:
        if e.errno == 2:
            raise DistutilsError('"%s" is not present on this system' % cmdline[0])
        else:
            raise
    if returncode != 0:
        raise DistutilsError('Got return value %d while executing "%s", stderr output was:\n%s' % (returncode, " ".join(cmdline), stderr.rstrip("\n")))
    return stdout


class cares_build_ext(build_ext):
    cares_dir = os.path.join('deps', 'c-ares')

    user_options = build_ext.user_options
    user_options.extend([
        ("cares-clean-compile", None, "Clean c-ares tree before compilation"),
    ])
    boolean_options = build_ext.boolean_options
    boolean_options.extend(["cares-clean-compile"])

    def initialize_options(self):
        build_ext.initialize_options(self)
        self.cares_clean_compile = 0

    def build_extensions(self):
        if self.compiler.compiler_type == 'mingw32':
            # Dirty hack to avoid linking with more than one C runtime when using MinGW
            self.compiler.dll_libraries = [lib for lib in self.compiler.dll_libraries if not lib.startswith('msvcr')]
        self.force = self.cares_clean_compile
        self.build_cares()
        build_ext.build_extensions(self)

    def finalize_options(self):
        build_ext.finalize_options(self)
        self.include_dirs.append(os.path.join(self.cares_dir, 'src'))
        self.library_dirs.append(self.cares_dir)
        self.libraries.append('cares')
        if sys.platform.startswith('linux'):
            self.libraries.append('rt')
        elif sys.platform == 'win32':
            self.libraries.append('iphlpapi')
            self.libraries.append('psapi')
            self.libraries.append('ws2_32')
            self.libraries.append('advapi32')

    def build_cares(self):
        #self.debug_mode =  bool(self.debug) or hasattr(sys, 'gettotalrefcount')
        win32_msvc = self.compiler.compiler_type == 'msvc'
        def build():
            cflags = '-fPIC'
            env = os.environ.copy()
            env['CFLAGS'] = ' '.join(x for x in (cflags, env.get('CFLAGS', None)) if x)
            log.info('Building c-ares...')
            if win32_msvc:
                exec_process(['nmake', '/f', 'Makefile.msvc'], cwd=self.cares_dir, env=env)
            else:
                exec_process(['make', 'libcares.a'], cwd=self.cares_dir, env=env)
        def clean():
            if win32_msvc:
                exec_process(['nmake', '/f', 'Makefile.msvc', 'clean'], cwd=self.cares_dir, env=env)
            else:
                exec_process(['make', 'clean'], cwd=self.cares_dir)
        if self.cares_clean_compile:
            clean()
        if not os.path.exists(os.path.join(self.cares_dir, 'libcares.a')):
            log.info('c-ares needs to be compiled.')
            build()
        else:
            log.info('No need to build c-ares.')

