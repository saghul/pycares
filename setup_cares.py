
import errno
import os
try:
    # backported python3 subprocess in python2
    import subprocess32 as subprocess
except:
    import subprocess
import sys
import io

from distutils import log
from distutils.command.build_ext import build_ext
from distutils.errors import DistutilsError


def exec_process(cmdline, silent=True, catch_enoent=True, input=None, **kwargs):
    """Execute a subprocess and returns the returncode, stdout buffer and stderr buffer.
    Optionally prints stdout and stderr while running."""
    try:
        sub = subprocess.Popen(args=cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        stdout, stderr = sub.communicate(input=input)

        if not isinstance(stdout, str):
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
    assert isinstance(cmdline, list)
    makes = ["make"]
    if "bsd" in sys.platform:
        makes.insert(0, "gmake")
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
        ("use-system-libcares", None, "Use the system provided libcares, instead of the bundled one"),
    ])
    boolean_options = build_ext.boolean_options
    boolean_options.extend(["cares-clean-compile", "use-system-libcares"])

    def initialize_options(self):
        build_ext.initialize_options(self)
        self.cares_clean_compile = 0
        self.use_system_libcares = 0

    def build_extensions(self):
        if self.use_system_libcares:
            pkg_config_version_check('libcares', libcares_version_required)
            runtime_library_dirs = pkg_config_parse('--libs-only-L',   'libcares')
            include_dirs         = pkg_config_parse('--cflags-only-I', 'libcares')
            library_dirs         = pkg_config_parse('--libs-only-L',   'libcares')
            libraries            = pkg_config_parse('--libs-only-l',   'libcares')
            log.debug(libraries)
            if libraries.len > 0:
                self.compiler.add_library(libraries)
            if library_dirs.len > 0:
                self.compiler.add_library_dir(library_dirs)
            if include_dirs.len > 0:
                self.compiler.set_include_dirs(include_dirs)
            if runtime_library_dirs.len > 0:
                self.compiler.set_runtime_library_dirs(runtime_library_dirs)
        else:
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
        # self.debug_mode =  bool(self.debug) or hasattr(sys, 'gettotalrefcount')
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


def call(command, opt=None):
    pipe = subprocess.Popen(command, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    pipe.wait()

    pipe.stdout = pipe.stdout.read()
    if pipe.stdout is not None:
        if not isinstance(stdout, str):
            # decode on Python 3
            # do nothing on Python 2 (it just doesn't care about encoding anyway)
            pipe.stdout = pipe.stdout.decode(sys.stdout.encoding)
        pipe.stdout = pipe.stdout.split()
        if opt is not None:
            pipe.stdout = [x.lstrip(opt) for x in pipe.stdout]
    pipe.stderr = pipe.stderr.read()
    if pipe.stderr is not None:
        if not isinstance(stdout, str):
            # decode on Python 3
            # do nothing on Python 2 (it just doesn't care about encoding anyway)
            pipe.stderr = pipe.stderr.decode(sys.stderr.encoding)
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
    if pipe.stdout is not None:
        return pipe.stdout
    else:
        return []
