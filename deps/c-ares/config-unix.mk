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

E=
CSTDFLAG=--std=c89 -pedantic -Wall -Wextra -Wno-unused-parameter
CFLAGS += -g
CPPFLAGS += -Iares
LINKFLAGS=-lm

CPPFLAGS += -D_LARGEFILE_SOURCE
CPPFLAGS += -D_FILE_OFFSET_BITS=64

ifeq (SunOS,$(uname_S))
CPPFLAGS += -Isrc/config_sunos -D__EXTENSIONS__ -D_XOPEN_SOURCE=500
LINKFLAGS+=-lsocket -lnsl -lkstat
endif

ifeq (Darwin,$(uname_S))
CPPFLAGS += -D_DARWIN_USE_64_BIT_INODE=1 -Isrc/config_darwin
endif

ifeq (Linux,$(uname_S))
CSTDFLAG += -D_GNU_SOURCE
CPPFLAGS += -Isrc/config_linux
LINKFLAGS+=-ldl -lrt
endif

ifeq (FreeBSD,$(uname_S))
CPPFLAGS += -Isrc/config_freebsd
LINKFLAGS+=-lkvm
endif

ifeq (DragonFly,$(uname_S))
CPPFLAGS += -Isrc/config_freebsd
endif

ifeq (NetBSD,$(uname_S))
CPPFLAGS += -Isrc/config_netbsd
endif

ifeq (OpenBSD,$(uname_S))
CPPFLAGS += -Isrc/config_openbsd
endif

ifneq (,$(findstring CYGWIN,$(uname_S)))
# We drop the --std=c89, it hides CLOCK_MONOTONIC on cygwin
CSTDFLAG = -D_GNU_SOURCE
CPPFLAGS += -Isrc/config_cygwin
endif

libcares.a: $(CARES_OBJS)
	$(AR) rcs libcares.a $^

