
import os
import sys
import subprocess
from distutils.spawn import find_executable

from setuptools.command.build_ext import build_ext

use_system_lib = bool(int(os.environ.get('PYCARES_USE_SYSTEM_LIB', 0)))


class cares_build_ext(build_ext):
    def add_include_dir(self, dir, force=False):
        if use_system_lib and not force:
            return
        dirs = self.compiler.include_dirs
        if dir not in dirs:
            dirs.insert(0, dir)
        self.compiler.set_include_dirs(dirs)

    def build_extensions(self):
        # Use system c-ares library if requested
        if use_system_lib:
            self.compiler.add_library('cares')
            build_ext.build_extensions(self)
            return

        # Check for CMake availability
        cmake_cmd = find_executable('cmake')
        if not cmake_cmd:
            raise RuntimeError(
                "CMake >= 3.5 is required to build pycares.\n"
                "Please install CMake from https://cmake.org/ or through your system package manager:\n"
                "  Ubuntu/Debian: apt-get install cmake\n"
                "  RHEL/CentOS/Fedora: dnf install cmake\n"
                "  macOS: brew install cmake\n"
                "  Windows: Download from https://cmake.org/download/\n"
                "  FreeBSD: pkg install cmake"
            )

        # Set up directories
        cares_dir = os.path.join('deps', 'c-ares')
        build_temp = os.path.abspath(os.path.join(self.build_temp, 'c-ares-build'))
        install_dir = os.path.abspath(os.path.join(self.build_temp, 'c-ares-install'))
        os.makedirs(build_temp, exist_ok=True)
        os.makedirs(install_dir, exist_ok=True)

        # Configure c-ares with CMake
        cmake_args = [
            '-DCARES_STATIC=ON',
            '-DCARES_SHARED=OFF',
            '-DCARES_BUILD_TOOLS=OFF',
            '-DCARES_BUILD_TESTS=OFF',
            '-DCARES_INSTALL=ON',
            '-DCARES_THREADS=ON',
            '-DCARES_STATIC_PIC=ON',  # Position independent code for static lib
            '-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_CONFIGURATION_TYPES=Release',  # For multi-config generators (VS, Xcode)
            f'-DCMAKE_INSTALL_PREFIX={install_dir}',
        ]

        # Platform-specific configuration
        if sys.platform == 'win32':
            # Windows-specific handling
            if 'mingw' in self.compiler.compiler_type:
                cmake_args.extend(['-G', 'MinGW Makefiles'])

            # Handle static runtime if needed
            if hasattr(self, 'compiler') and hasattr(self.compiler, 'compile_options'):
                for flag in self.compiler.compile_options:
                    if '/MT' in str(flag):
                        cmake_args.append('-DCARES_MSVC_STATIC_RUNTIME=ON')
                        break

        # Run CMake configure
        print(f"Configuring c-ares with CMake in {build_temp}")
        subprocess.check_call(
            [cmake_cmd, os.path.abspath(cares_dir)] + cmake_args,
            cwd=build_temp
        )

        # Build c-ares
        print("Building c-ares...")
        build_args = ['--build', '.', '--config', 'Release']

        # Use parallel build if available
        if sys.platform != 'win32':
            try:
                import multiprocessing
                build_args.extend(['--parallel', str(multiprocessing.cpu_count())])
            except (ImportError, NotImplementedError):
                pass

        subprocess.check_call([cmake_cmd] + build_args, cwd=build_temp)

        # Install c-ares to temp directory
        print(f"Installing c-ares to {install_dir}")
        install_args = ['--install', '.', '--config', 'Release']
        subprocess.check_call([cmake_cmd] + install_args, cwd=build_temp)

        # Find the installed library
        if sys.platform == 'win32':
            # Windows libraries
            possible_paths = [
                os.path.join(install_dir, 'lib', 'cares.lib'),
                os.path.join(install_dir, 'lib', 'cares_static.lib'),
                os.path.join(install_dir, 'lib', 'libcares.a'),  # MinGW
            ]
        else:
            possible_paths = [
                os.path.join(install_dir, 'lib', 'libcares.a'),
                os.path.join(install_dir, 'lib64', 'libcares.a'),
            ]

        lib_path = None
        for path in possible_paths:
            if os.path.exists(path):
                lib_path = path
                break

        if not lib_path:
            raise RuntimeError(
                f"Could not find installed c-ares library in {install_dir}.\n"
                f"Checked: {', '.join(possible_paths)}"
            )

        print(f"Found c-ares library at: {lib_path}")

        # Set up include directories from the install directory
        # This includes all headers (original + generated like ares_build.h, ares_config.h)
        self.add_include_dir(os.path.join(install_dir, 'include'), force=True)
        # Also need internal headers from src/lib for some definitions
        self.add_include_dir(os.path.join(cares_dir, 'src', 'lib'), force=True)

        # Set up the extension to link against the static library
        self.extensions[0].extra_objects = [lib_path]

        # Add platform-specific libraries and macros
        if sys.platform == 'win32':
            self.compiler.add_library('ws2_32')
            self.compiler.add_library('advapi32')
            self.compiler.add_library('iphlpapi')
            self.compiler.define_macro('CARES_STATICLIB', 1)
        else:
            self.compiler.define_macro('HAVE_CONFIG_H', 1)
            self.compiler.define_macro('_LARGEFILE_SOURCE', 1)
            self.compiler.define_macro('_FILE_OFFSET_BITS', 64)
            self.compiler.define_macro('CARES_STATICLIB', 1)

            if sys.platform.startswith('linux'):
                self.compiler.add_library('rt')
            elif sys.platform == 'darwin':
                self.compiler.define_macro('_DARWIN_USE_64_BIT_INODE', 1)
            elif sys.platform.startswith('freebsd') or sys.platform.startswith('dragonfly'):
                self.compiler.add_library('kvm')
            elif sys.platform.startswith('sunos'):
                self.compiler.add_library('socket')
                self.compiler.add_library('nsl')
                self.compiler.add_library('kstat')

        # Build the Python extension
        build_ext.build_extensions(self)
