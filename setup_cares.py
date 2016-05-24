
import errno
import os
import subprocess
import sys

from distutils import log
from distutils.command.build_ext import build_ext
from distutils.errors import DistutilsError

cares_sources = [
    'deps/c-ares/src/ares__close_sockets.c',
    'deps/c-ares/src/ares__get_hostent.c',
    'deps/c-ares/src/ares__read_line.c',
    'deps/c-ares/src/ares__timeval.c',
    'deps/c-ares/src/ares_cancel.c',
    'deps/c-ares/src/ares_create_query.c',
    'deps/c-ares/src/ares_data.c',
    'deps/c-ares/src/ares_destroy.c',
    'deps/c-ares/src/ares_expand_name.c',
    'deps/c-ares/src/ares_expand_string.c',
    'deps/c-ares/src/ares_fds.c',
    'deps/c-ares/src/ares_free_hostent.c',
    'deps/c-ares/src/ares_free_string.c',
    'deps/c-ares/src/ares_gethostbyaddr.c',
    'deps/c-ares/src/ares_gethostbyname.c',
    'deps/c-ares/src/ares_getnameinfo.c',
    'deps/c-ares/src/ares_getopt.c',
    'deps/c-ares/src/ares_getsock.c',
    'deps/c-ares/src/ares_init.c',
    'deps/c-ares/src/ares_library_init.c',
    'deps/c-ares/src/ares_llist.c',
    'deps/c-ares/src/ares_mkquery.c',
    'deps/c-ares/src/ares_nowarn.c',
    'deps/c-ares/src/ares_options.c',
    'deps/c-ares/src/ares_parse_a_reply.c',
    'deps/c-ares/src/ares_parse_aaaa_reply.c',
    'deps/c-ares/src/ares_parse_mx_reply.c',
    'deps/c-ares/src/ares_parse_naptr_reply.c',
    'deps/c-ares/src/ares_parse_ns_reply.c',
    'deps/c-ares/src/ares_parse_ptr_reply.c',
    'deps/c-ares/src/ares_parse_soa_reply.c',
    'deps/c-ares/src/ares_parse_srv_reply.c',
    'deps/c-ares/src/ares_parse_txt_reply.c',
    'deps/c-ares/src/ares_process.c',
    'deps/c-ares/src/ares_query.c',
    'deps/c-ares/src/ares_search.c',
    'deps/c-ares/src/ares_send.c',
    'deps/c-ares/src/ares_strcasecmp.c',
    'deps/c-ares/src/ares_strdup.c',
    'deps/c-ares/src/ares_strerror.c',
    'deps/c-ares/src/ares_timeout.c',
    'deps/c-ares/src/ares_version.c',
    'deps/c-ares/src/ares_writev.c',
    'deps/c-ares/src/bitncmp.c',
    'deps/c-ares/src/inet_net_pton.c',
    'deps/c-ares/src/inet_ntop.c',
]


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

    def build_extensions(self):
        if self.compiler.compiler_type == 'mingw32':
            # Dirty hack to avoid linking with more than one C runtime when using MinGW
            self.compiler.dll_libraries = [lib for lib in self.compiler.dll_libraries if not lib.startswith('msvcr')]
        self.build_cares()
        # Set compiler options
        if self.compiler.compiler_type == 'mingw32':
            self.compiler.add_library_dir(self.cares_dir)
            self.compiler.add_library('cares')
        #self.extensions[0].extra_objects = [self.cares_lib]
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
        self.compiler.define_macro('HAVE_CONFIG_H', 1)
        if sys.platform == 'win32':
            global cares_sources
            cares_sources += ['deps/c-ares/src/windows_port.c',
                              'deps/c-ares/src/ares_platform.c']
            self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_win32'))
            #-D_WIN32_WINNT=0x0600 

        else:
            self.compiler.define_macro('_LARGEFILE_SOURCE', 1)
            self.compiler.define_macro('_FILE_OFFSET_BITS', 64)

            if sys.platform.startswith('linux'):
                self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_linux'))

        self.extensions[0].sources += cares_sources

