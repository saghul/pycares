# Copyright Joyent, Inc. and other Node contributors. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

uname_S := $(shell sh -c 'uname -s 2>/dev/null || echo not')

ifdef MSVC
uname_S := MINGW
endif

CPPFLAGS += -Isrc

CARES_OBJS =
CARES_OBJS += src/ares__close_sockets.o
CARES_OBJS += src/ares__get_hostent.o
CARES_OBJS += src/ares__read_line.o
CARES_OBJS += src/ares__timeval.o
CARES_OBJS += src/ares_cancel.o
CARES_OBJS += src/ares_create_query.o
CARES_OBJS += src/ares_data.o
CARES_OBJS += src/ares_destroy.o
CARES_OBJS += src/ares_expand_name.o
CARES_OBJS += src/ares_expand_string.o
CARES_OBJS += src/ares_fds.o
CARES_OBJS += src/ares_free_hostent.o
CARES_OBJS += src/ares_free_string.o
CARES_OBJS += src/ares_gethostbyaddr.o
CARES_OBJS += src/ares_gethostbyname.o
CARES_OBJS += src/ares_getnameinfo.o
CARES_OBJS += src/ares_getopt.o
CARES_OBJS += src/ares_getsock.o
CARES_OBJS += src/ares_init.o
CARES_OBJS += src/ares_library_init.o
CARES_OBJS += src/ares_llist.o
CARES_OBJS += src/ares_nowarn.o
CARES_OBJS += src/ares_options.o
CARES_OBJS += src/ares_parse_a_reply.o
CARES_OBJS += src/ares_parse_aaaa_reply.o
CARES_OBJS += src/ares_parse_mx_reply.o
CARES_OBJS += src/ares_parse_naptr_reply.o
CARES_OBJS += src/ares_parse_ns_reply.o
CARES_OBJS += src/ares_parse_ptr_reply.o
CARES_OBJS += src/ares_parse_soa_reply.o
CARES_OBJS += src/ares_parse_srv_reply.o
CARES_OBJS += src/ares_parse_txt_reply.o
CARES_OBJS += src/ares_process.o
CARES_OBJS += src/ares_query.o
CARES_OBJS += src/ares_search.o
CARES_OBJS += src/ares_send.o
CARES_OBJS += src/ares_strcasecmp.o
CARES_OBJS += src/ares_strdup.o
CARES_OBJS += src/ares_strerror.o
CARES_OBJS += src/ares_timeout.o
CARES_OBJS += src/ares_version.o
CARES_OBJS += src/ares_writev.o
CARES_OBJS += src/bitncmp.o
CARES_OBJS += src/inet_net_pton.o
CARES_OBJS += src/inet_ntop.o

ifneq (,$(findstring MINGW,$(uname_S)))
include config-mingw.mk
else
include config-unix.mk
endif

all: libcares.a

$(CARES_OBJS): %.o: %.c
	$(CC) -o $*.o -c $(CFLAGS) $(CPPFLAGS) $< -DHAVE_CONFIG_H


.PHONY: clean distclean

clean:
	$(RM) -f src/*.o *.a

distclean:
	$(RM) -f src/*.o *.a

