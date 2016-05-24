
import os
import sys

from distutils.command.build_ext import build_ext


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

if sys.platform == 'win32':
    cares_sources += ['deps/c-ares/src/windows_port.c',
                      'deps/c-ares/src/ares_platform.c']


class cares_build_ext(build_ext):
    cares_dir = os.path.join('deps', 'c-ares')

    def build_extensions(self):
        self.compiler.define_macro('HAVE_CONFIG_H', 1)
        self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src'))
        if sys.platform != 'win32':
            self.compiler.define_macro('_LARGEFILE_SOURCE', 1)
            self.compiler.define_macro('_FILE_OFFSET_BITS', 64)
        if sys.platform.startswith('linux'):
            self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_linux'))
            self.compiler.add_library('dl')
            self.compiler.add_library('rt')
        elif sys.platform == 'darwin':
            self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_darwin'))
            self.compiler.define_macro('_DARWIN_USE_64_BIT_INODE', 1)
        elif sys.platform.startswith('freebsd'):
            self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_freebsd'))
            self.compiler.add_library('kvm')
        elif sys.platform.startswith('dragonfly'):
            self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_freebsd'))
        elif sys.platform.startswith('netbsd'):
            self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_netbsd'))
        elif sys.platform.startswith('openbsd'):
            self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_openbsd'))
        elif sys.platform.startswith('sunos'):
            self.compiler.add_library('socket')
            self.compiler.add_library('nsl')
            self.compiler.add_library('lkstat')
        elif sys.platform == 'win32':
            self.compiler.add_include_dir(os.path.join(self.cares_dir, 'src/config_win32'))
            self.extensions[0].extra_link_args = ['/NODEFAULTLIB:libcmt']
            self.compiler.add_library('advapi32')
            self.compiler.add_library('iphlpapi')
            self.compiler.add_library('psapi')
            self.compiler.add_library('ws2_32')
        self.extensions[0].sources += cares_sources
        build_ext.build_extensions(self)
