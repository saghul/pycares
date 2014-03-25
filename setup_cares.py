
import os
import subprocess
import sys
import errno

from distutils import log
from distutils.command.build_ext import build_ext
from distutils.errors import DistutilsError


def exec_process(cmdline, silent=True, catch_enoent=True, input=None, **kwargs):
    """Execute a subprocess and returns the returncode, stdout buffer and stderr buffer.
    Optionally prints stdout and stderr while running."""
    try:
        sub = subprocess.Popen(args=cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        stdout, stderr = sub.communicate(input=input)

        if type(stdout) != type(""):
            # decode on Python 3
            # do nothing on Python 2 (it just doesn't care about encoding anyway)
            stdout = stdout.decode(sys.getdefaultencoding(), "replace")
            stderr = stderr.decode(sys.getdefaultencoding(), "replace")

        returncode = sub.returncode
        if not silent:
            sys.stdout.write(stdout)
            sys.stderr.write(stderr)
    except OSError as e:
        if e.errno == errno.ENOENT and catch_enoent:
            raise DistutilsError('"%s" is not present on this system' % cmdline[0])
        else:
            raise
    if returncode != 0:
        raise DistutilsError('Got return value %d while executing "%s", stderr output was:\n%s' % (returncode, " ".join(cmdline), stderr.rstrip("\n")))
    return stdout

def exec_make(cmdline, *args, **kwargs):
    # our makefiles use several GNU extensions
    # so try 'gmake' first, and if it doesn't exist, 'make'
    # on FreeBSD, 'make' is BSD make, GNU make has to be installed from ports 
    # on GNU/Linux, 'make' is GNU make, and 'gmake' doesn't always exist 
    # (if it does, it's an alias for make, so no problem here)
    makes = ["gmake", "make"]

    assert isinstance(cmdline, list)

    for make in makes:

        if "bsd" in sys.platform and make == "make":
            log.warn("Running plain make on BSD-derived system. It will likely fail. Consider installing GNU make from the ports collection.")

        try:
            return exec_process([make] + cmdline, *args, catch_enoent=False, **kwargs)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
    
    raise DistutilsError('"make" is not present on this system')

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
        if self.compiler.compiler_type == 'msvc':
            self.cares_lib = os.path.join(self.cares_dir, 'cares.lib')
        else:
            self.cares_lib = os.path.join(self.cares_dir, 'libcares.a')
        self.build_cares()
        # Set compiler options
        if self.compiler.compiler_type == 'mingw32':
            self.compiler.add_library_dir(self.cares_dir)
            self.compiler.add_library('cares')
        self.extensions[0].extra_objects = [self.cares_lib]
        self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src'))
        if sys.platform.startswith('linux'):
            self.compiler.add_library('rt')
        elif sys.platform == 'win32':
            if self.compiler.compiler_type == 'msvc':
                self.extensions[0].extra_link_args = ['/NODEFAULTLIB:libcmt']
                self.compiler.add_library('advapi32')
            self.compiler.add_library('iphlpapi')
            self.compiler.add_library('psapi')
            self.compiler.add_library('ws2_32')
        build_ext.build_extensions(self)

    def build_cares(self):
        #self.debug_mode =  bool(self.debug) or hasattr(sys, 'gettotalrefcount')
        win32_msvc = self.compiler.compiler_type == 'msvc'
        def build():
            cflags = '-fPIC'
            env = os.environ.copy()
            env['CFLAGS'] = ' '.join(x for x in (cflags, env.get('CFLAGS', None)) if x)
            log.info('Building c-ares...')
            if win32_msvc:
                exec_process('cmd.exe /C vcbuild.bat', cwd=self.cares_dir, env=env, shell=True)
            else:
                exec_make(['libcares.a'], cwd=self.cares_dir, env=env)
                    
        def clean():
            if win32_msvc:
                exec_process('cmd.exe /C vcbuild.bat clean', cwd=self.cares_dir, shell=True)
            else:
                exec_make(['clean'], cwd=self.cares_dir)
        if self.cares_clean_compile:
            clean()
        if not os.path.exists(self.cares_lib):
            log.info('c-ares needs to be compiled.')
            build()
        else:
            log.info('No need to build c-ares.')

