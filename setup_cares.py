
import os
import sys

from setuptools.command.build_ext import build_ext

use_system_lib = bool(int(os.environ.get('PYCARES_USE_SYSTEM_LIB', 0)))

cares_sources = [
    'deps/c-ares/src/lib/ares__addrinfo2hostent.c',
    'deps/c-ares/src/lib/ares__addrinfo_localhost.c',
    'deps/c-ares/src/lib/ares__close_sockets.c',
    'deps/c-ares/src/lib/ares__get_hostent.c',
    'deps/c-ares/src/lib/ares__parse_into_addrinfo.c',
    'deps/c-ares/src/lib/ares__read_line.c',
    'deps/c-ares/src/lib/ares__readaddrinfo.c',
    'deps/c-ares/src/lib/ares__sortaddrinfo.c',
    'deps/c-ares/src/lib/ares__timeval.c',
    'deps/c-ares/src/lib/ares_android.c',
    'deps/c-ares/src/lib/ares_cancel.c',
    'deps/c-ares/src/lib/ares_create_query.c',
    'deps/c-ares/src/lib/ares_data.c',
    'deps/c-ares/src/lib/ares_destroy.c',
    'deps/c-ares/src/lib/ares_expand_name.c',
    'deps/c-ares/src/lib/ares_expand_string.c',
    'deps/c-ares/src/lib/ares_fds.c',
    'deps/c-ares/src/lib/ares_free_hostent.c',
    'deps/c-ares/src/lib/ares_free_string.c',
    'deps/c-ares/src/lib/ares_freeaddrinfo.c',
    'deps/c-ares/src/lib/ares_getaddrinfo.c',
    'deps/c-ares/src/lib/ares_getenv.c',
    'deps/c-ares/src/lib/ares_gethostbyaddr.c',
    'deps/c-ares/src/lib/ares_gethostbyname.c',
    'deps/c-ares/src/lib/ares_getnameinfo.c',
    'deps/c-ares/src/lib/ares_getsock.c',
    'deps/c-ares/src/lib/ares_init.c',
    'deps/c-ares/src/lib/ares_library_init.c',
    'deps/c-ares/src/lib/ares_llist.c',
    'deps/c-ares/src/lib/ares_mkquery.c',
    'deps/c-ares/src/lib/ares_nowarn.c',
    'deps/c-ares/src/lib/ares_options.c',
    'deps/c-ares/src/lib/ares_parse_a_reply.c',
    'deps/c-ares/src/lib/ares_parse_aaaa_reply.c',
    'deps/c-ares/src/lib/ares_parse_caa_reply.c',
    'deps/c-ares/src/lib/ares_parse_mx_reply.c',
    'deps/c-ares/src/lib/ares_parse_naptr_reply.c',
    'deps/c-ares/src/lib/ares_parse_ns_reply.c',
    'deps/c-ares/src/lib/ares_parse_ptr_reply.c',
    'deps/c-ares/src/lib/ares_parse_soa_reply.c',
    'deps/c-ares/src/lib/ares_parse_srv_reply.c',
    'deps/c-ares/src/lib/ares_parse_txt_reply.c',
    'deps/c-ares/src/lib/ares_process.c',
    'deps/c-ares/src/lib/ares_query.c',
    'deps/c-ares/src/lib/ares_search.c',
    'deps/c-ares/src/lib/ares_send.c',
    'deps/c-ares/src/lib/ares_strcasecmp.c',
    'deps/c-ares/src/lib/ares_strdup.c',
    'deps/c-ares/src/lib/ares_strerror.c',
    'deps/c-ares/src/lib/ares_strsplit.c',
    'deps/c-ares/src/lib/ares_timeout.c',
    'deps/c-ares/src/lib/ares_version.c',
    'deps/c-ares/src/lib/ares_writev.c',
    'deps/c-ares/src/lib/bitncmp.c',
    'deps/c-ares/src/lib/inet_net_pton.c',
    'deps/c-ares/src/lib/inet_ntop.c',
]

if sys.platform == 'win32':
    cares_sources += ['deps/c-ares/src/lib/windows_port.c',
                      'deps/c-ares/src/lib/ares_platform.c']


class cares_build_ext(build_ext):
    cares_dir = os.path.join('deps', 'c-ares')
    build_config_dir = os.path.join('deps', 'build-config')

    def add_include_dir(self, dir, force=False):
        if use_system_lib and not force:
            return
        dirs = self.compiler.include_dirs
        dirs.insert(0, dir)
        self.compiler.set_include_dirs(dirs)

    def build_extensions(self):
        self.add_include_dir(os.path.join(self.cares_dir, 'include'))
        self.add_include_dir(os.path.join(self.build_config_dir, 'include'), True)
        if sys.platform != 'win32':
            self.compiler.define_macro('HAVE_CONFIG_H', 1)
            self.compiler.define_macro('_LARGEFILE_SOURCE', 1)
            self.compiler.define_macro('_FILE_OFFSET_BITS', 64)
        if sys.platform.startswith('linux'):
            # Check if it's actually Android
            if os.environ.get('ANDROID_ROOT') and os.environ.get('ANDROID_DATA'):
                self.add_include_dir(os.path.join(self.build_config_dir, 'config_android'))
            else:
                self.add_include_dir(os.path.join(self.build_config_dir, 'config_linux'))
            self.compiler.add_library('dl')
            self.compiler.add_library('rt')
        elif sys.platform == 'darwin':
            self.add_include_dir(os.path.join(self.build_config_dir, 'config_darwin'))
            self.compiler.define_macro('_DARWIN_USE_64_BIT_INODE', 1)
        elif sys.platform.startswith('freebsd'):
            self.add_include_dir(os.path.join(self.build_config_dir, 'config_freebsd'))
            self.compiler.add_library('kvm')
        elif sys.platform.startswith('dragonfly'):
            self.add_include_dir(os.path.join(self.build_config_dir, 'config_freebsd'))
        elif sys.platform.startswith('netbsd'):
            self.add_include_dir(os.path.join(self.build_config_dir, 'config_netbsd'))
        elif sys.platform.startswith('openbsd'):
            self.add_include_dir(os.path.join(self.build_config_dir, 'config_openbsd'))
        elif sys.platform.startswith('sunos'):
            self.add_include_dir(os.path.join(self.build_config_dir, 'config_sunos'))
            self.compiler.add_library('socket')
            self.compiler.add_library('nsl')
            self.compiler.add_library('kstat')
        elif sys.platform == 'cygwin':
            self.add_include_dir(os.path.join(self.build_config_dir, 'config_cygwin'))
        elif sys.platform == 'win32':
            if 'mingw' not in self.compiler.compiler_type:
                self.extensions[0].extra_link_args = ['/NODEFAULTLIB:libcmt']
            self.compiler.add_library('advapi32')
            self.compiler.add_library('iphlpapi')
            self.compiler.add_library('psapi')
            self.compiler.add_library('ws2_32')
            self.compiler.define_macro('CARES_PULL_WS2TCPIP_H', 1)

        if use_system_lib:
            self.compiler.add_library('cares')
        else:
            self.compiler.define_macro('CARES_STATICLIB', 1)
            self.extensions[0].sources += cares_sources

        build_ext.build_extensions(self)
