#!/usr/bin/env python

import functools
import gc
import ipaddress
import os
import select
import socket
import sys
import unittest
import threading
import time
import weakref
import pycares

FIXTURES_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), 'fixtures'))


class DNSTest(unittest.TestCase):

    def setUp(self):
        self.channel = pycares.Channel(timeout=10.0, tries=1, servers=['8.8.8.8', '8.8.4.4'])
        self.is_ci = os.environ.get('APPVEYOR') or os.environ.get('TRAVIS') or os.environ.get('GITHUB_ACTION')

    def tearDown(self):
        self.channel = None

    def wait(self):
        while True:
            read_fds, write_fds = self.channel.getsock()
            if not read_fds and not write_fds:
                break
            timeout = self.channel.timeout()
            if timeout == 0.0:
                self.channel.process_fd(pycares.ARES_SOCKET_BAD, pycares.ARES_SOCKET_BAD)
                continue
            rlist, wlist, xlist = select.select(read_fds, write_fds, [], timeout)
            for fd in rlist:
                self.channel.process_fd(fd, pycares.ARES_SOCKET_BAD)
            for fd in wlist:
                self.channel.process_fd(pycares.ARES_SOCKET_BAD, fd)

    def assertNoError(self, errorno):
        if errorno == pycares.errno.ARES_ETIMEOUT and self.is_ci:
            raise unittest.SkipTest('timeout')
        self.assertEqual(errorno, None)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_getaddrinfo(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getaddrinfo('localhost', 80, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_addrinfo_result)
        self.assertTrue(len(self.result.nodes) > 0)
        for node in self.result.nodes:
            self.assertEqual(node.addr[1], 80)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_getaddrinfo2(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getaddrinfo('localhost', 'http', cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_addrinfo_result)
        self.assertTrue(len(self.result.nodes) > 0)
        for node in self.result.nodes:
            self.assertEqual(node.addr[1], 80)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_getaddrinfo3(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getaddrinfo('localhost', None, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_addrinfo_result)
        self.assertTrue(len(self.result.nodes) > 0)
        for node in self.result.nodes:
            self.assertEqual(node.addr[1], 0)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_getaddrinfo4(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getaddrinfo('localhost', 'http', cb, family=socket.AF_INET)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_addrinfo_result)
        self.assertEqual(len(self.result.nodes), 1)
        node = self.result.nodes[0]
        self.assertEqual(node.addr[0], b'127.0.0.1')
        self.assertEqual(node.addr[1], 80)

    def test_getaddrinfo5(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getaddrinfo('google.com', 'http', cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_addrinfo_result)
        self.assertTrue(len(self.result.nodes) > 0)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyaddr(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.gethostbyaddr('127.0.0.1', cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyaddr6(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.gethostbyaddr('::1', cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyname(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.gethostbyname('localhost', socket.AF_INET, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyname_small_timeout(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(timeout=0.5, tries=1)
        self.channel.gethostbyname('localhost', socket.AF_INET, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_getnameinfo(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getnameinfo(('127.0.0.1', 80), pycares.ARES_NI_LOOKUPHOST|pycares.ARES_NI_LOOKUPSERVICE, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_nameinfo_result)
        self.assertIn(self.result.node, ('localhost.localdomain', 'localhost'))
        self.assertEqual(self.result.service, 'http')

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    @unittest.expectedFailure  # c-ares is broken (does not return numeric service if asked) and unconditionally adds zero scope
    def test_getnameinfo_ipv6(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getnameinfo(('fd01:dec0:0:1::2020', 80, 0, 0), pycares.ARES_NI_NUMERICHOST|pycares.ARES_NI_NUMERICSERV, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_nameinfo_result)
        self.assertEqual(self.result.node, 'fd01:dec0:0:1::2020')
        self.assertEqual(self.result.service, '80')

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    @unittest.expectedFailure  # c-ares is broken (does not return numeric service if asked)
    def test_getnameinfo_ipv6_ll(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getnameinfo(('fe80::5abd:fee7:4177:60c0', 80, 0, 666), pycares.ARES_NI_NUMERICHOST|pycares.ARES_NI_NUMERICSERV|pycares.ARES_NI_NUMERICSCOPE, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_nameinfo_result)
        self.assertEqual(self.result.node, 'fe80::5abd:fee7:4177:60c0%666')
        self.assertEqual(self.result.service, '80')

    def test_query_a(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_a_result)
            self.assertNotEqual(r.host, None)

    def test_query_a_bad(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('hgf8g2od29hdohid.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.result, None)
        self.assertEqual(self.errorno, pycares.errno.ARES_ENOTFOUND)

    def test_query_a_rotate(self):
        self.result, self.errorno = None, None
        self.errorno_count, self.count = 0, 0
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
            if errorno:
                self.errorno_count += 1
            self.count += 1
        self.channel = pycares.Channel(timeout=1.0, tries=1, rotate=True)
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.count, 3)
        self.assertEqual(self.errorno_count, 0)

    def test_query_aaaa(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('ipv6.google.com', pycares.QUERY_TYPE_AAAA, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_aaaa_result)
            self.assertNotEqual(r.host, None)

    def test_query_caa(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('wikipedia.org', pycares.QUERY_TYPE_CAA, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertTrue(len(self.result) > 0)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_caa_result)

    def test_query_cname(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('www.amazon.com', pycares.QUERY_TYPE_CNAME, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_query_cname_result)

    def test_query_mx(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_MX, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_mx_result)

    def test_query_ns(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_NS, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_ns_result)

    def test_query_txt(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_txt_result)

    def test_query_txt_chunked(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('jobscoutdaily.com', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertNoError(self.errorno)
        # If the chunks are aggregated, only one TXT record should be visible. Three would show if they are not properly merged.
        # jobscoutdaily.com.    21600   IN  TXT "v=spf1 A MX " " ~all"
        self.assertEqual(self.result[0].text, 'v=spf1 A MX  ~all')

    def test_query_txt_multiple_chunked(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertNoError(self.errorno)
        # > dig -t txt google.com
        # google.com.		3270	IN	TXT	"google-site-verification=TV9-DBe4R80X4v0M4U_bd_J9cpOJM0nikft0jAgjmsQ"
        # google.com.		3270	IN	TXT	"atlassian-domain-verification=5YjTmWmjI92ewqkx2oXmBaD60Td9zWon9r6eakvHX6B77zzkFQto8PQ9QsKnbf4I"
        # google.com.		3270	IN	TXT	"docusign=05958488-4752-4ef2-95eb-aa7ba8a3bd0e"
        # google.com.		3270	IN	TXT	"facebook-domain-verification=22rm551cu4k0ab0bxsw536tlds4h95"
        # google.com.		3270	IN	TXT	"google-site-verification=wD8N7i1JTNTkezJ49swvWW48f8_9xveREV4oB-0Hf5o"
        # google.com.		3270	IN	TXT	"apple-domain-verification=30afIBcvSuDV2PLX"
        # google.com.		3270	IN	TXT	"webexdomainverification.8YX6G=6e6922db-e3e6-4a36-904e-a805c28087fa"
        # google.com.		3270	IN	TXT	"MS=E4A68B9AB2BB9670BCE15412F62916164C0B20BB"
        # google.com.		3270	IN	TXT	"v=spf1 include:_spf.google.com ~all"
        # google.com.		3270	IN	TXT	"globalsign-smime-dv=CDYX+XFHUw2wml6/Gb8+59BsH31KzUr6c1l2BPvqKX8="
        # google.com.		3270	IN	TXT	"docusign=1b0a6754-49b1-4db5-8540-d2c12664b289"
        self.assertGreater(len(self.result), 10)

    def test_query_txt_bytes1(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_txt_result)
            self.assertIsInstance(r.text, str)  # it's ASCII

    # The 2 tests below hit a dead end thus fail. Commenting for now as I couldn't find a live server
    # that satisfies what the tests are looking for

    # FIXME: wide.com.es is a dead end!
    @unittest.expectedFailure
    def test_query_txt_bytes2(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('wide.com.es', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_txt_result)
            self.assertIsInstance(r.text, bytes)

    # FIXME: "txt-non-ascii.dns-test.hmnid.ru" is a dead end!
    @unittest.expectedFailure
    def test_query_txt_multiple_chunked_with_non_ascii_content(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('txt-non-ascii.dns-test.hmnid.ru', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertNoError(self.errorno)
        # txt-non-ascii.dns-test.hmnid.ru.        IN      TXT     "ascii string" "some\208misc\208stuff"

        self.assertEqual(len(self.result), 1)
        r = self.result[0]
        self.assertEqual(type(r), pycares.ares_query_txt_result)
        self.assertIsInstance(r.text, bytes)

    def test_query_class_chaos(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno

        self.channel.servers = ['199.7.83.42']  # l.root-servers.net
        self.channel.query('id.server', pycares.QUERY_TYPE_TXT, cb, pycares.QUERY_CLASS_CHAOS)
        self.wait()
        self.assertNoError(self.errorno)
        # id.server.              0       CH      TXT     "aa.de-ham.l.root"

        self.assertEqual(len(self.result), 1)
        r = self.result[0]
        self.assertEqual(type(r), pycares.ares_query_txt_result)
        self.assertIsInstance(r.text, str)

    def test_query_class_invalid(self):
        self.assertRaises(ValueError, self.channel.query, 'google.com', pycares.QUERY_TYPE_A, lambda *x: None, "INVALIDTYPE")
        self.wait()

    def test_query_soa(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_SOA, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_query_soa_result)

    def test_query_srv(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('_xmpp-server._tcp.jabber.org', pycares.QUERY_TYPE_SRV, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_srv_result)

    def test_query_naptr(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('sip2sip.info', pycares.QUERY_TYPE_NAPTR, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_naptr_result)

    def test_query_ptr(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        ip = '172.253.122.26'
        self.channel.query(ipaddress.ip_address(ip).reverse_pointer, pycares.QUERY_TYPE_PTR, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_query_ptr_result)
        self.assertEqual(type(self.result.aliases), list)

    def test_query_ptr_ipv6(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        ip = '2001:4860:4860::8888'
        self.channel.query(ipaddress.ip_address(ip).reverse_pointer, pycares.QUERY_TYPE_PTR, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_query_ptr_result)
        self.assertEqual(type(self.result.aliases), list)

    @unittest.skip("ANY type does not work on Mac.")
    def test_query_any(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_ANY, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertTrue(len(self.result) > 1)

    def test_query_cancelled(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_NS, cb)
        self.channel.cancel()
        self.wait()
        self.assertEqual(self.result, None)
        self.assertEqual(self.errorno, pycares.errno.ARES_ECANCELLED)

    def test_reinit(self):
        servers = self.channel.servers
        self.channel.reinit()
        self.assertEqual(servers, self.channel.servers)

    def test_query_bad_type(self):
        self.assertRaises(ValueError, self.channel.query, 'google.com', 667, lambda *x: None)
        self.wait()

    def test_query_timeout(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.servers = ['1.2.3.4']
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.result, None)
        self.assertEqual(self.errorno, pycares.errno.ARES_ETIMEOUT)

    def test_query_onion(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('foo.onion', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.result, None)
        self.assertEqual(self.errorno, pycares.errno.ARES_ENOTFOUND)

    def test_channel_nameservers(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(timeout=5.0, tries=1, servers=['8.8.8.8'])
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertNoError(self.errorno)

    def test_channel_nameservers2(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.servers = ['8.8.8.8']
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertNoError(self.errorno)

    def test_channel_nameservers3(self):
        servers = ['8.8.8.8', '8.8.4.4']
        self.channel.servers = servers
        servers2 = self.channel.servers
        self.assertEqual(servers, servers2)

    def test_channel_local_ip(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(timeout=5.0, tries=1, servers=['8.8.8.8'], local_ip='127.0.0.1')
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.result, None)
        # May raise ECONNREFUSED or ETIMEDOUT depending on the platform
        self.assertIn(self.errorno, (pycares.errno.ARES_ECONNREFUSED, pycares.errno.ARES_ETIMEOUT))

    def test_channel_local_ip2(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.servers = ['8.8.8.8']
        self.channel.set_local_ip('127.0.0.1')
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.result, None)
        # May raise ECONNREFUSED or ETIMEDOUT depending on the platform
        self.assertIn(self.errorno, (pycares.errno.ARES_ECONNREFUSED, pycares.errno.ARES_ETIMEOUT))
        self.assertRaises(ValueError, self.channel.set_local_ip, 'an invalid ip')

    def test_channel_timeout(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(timeout=0.5, tries=1)
        self.channel.gethostbyname('google.com', socket.AF_INET, cb)
        timeout = self.channel.timeout()
        self.assertTrue(timeout > 0.0)
        self.channel.cancel()
        self.wait()
        self.assertEqual(self.result, None)
        self.assertEqual(self.errorno, pycares.errno.ARES_ECANCELLED)

    def test_import_errno(self):
        from pycares.errno import ARES_SUCCESS
        self.assertTrue(True)

    # FIXME
    @unittest.skip("The site used for this test no longer returns a non-ascii SOA.")
    def test_result_not_ascii(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('ayesas.com', pycares.QUERY_TYPE_SOA, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_query_soa_result)
        self.assertIsInstance(self.result.hostmaster, bytes)  # it's not ASCII

    def test_idna_encoding(self):
        host = 'españa.icom.museum'
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        # try encoding it as utf-8
        self.channel.gethostbyname(host.encode(), socket.AF_INET, cb)
        self.wait()
        self.assertNotEqual(self.errorno, None)
        self.assertEqual(self.result, None)
        # use it as is (it's IDNA encoded internally)
        self.channel.gethostbyname(host, socket.AF_INET, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    def test_idna_encoding_query_a(self):
        host = 'españa.icom.museum'
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        # try encoding it as utf-8
        self.channel.query(host.encode(), pycares.QUERY_TYPE_A, cb)
        self.wait()
        # ARES_EBADNAME correct for c-ares 1.24 and ARES_ENOTFOUND for 1.18
        # in 1.32.0 it was changed to ARES_ENOMEM
        if self.errorno in (pycares.errno.ARES_ENOTFOUND, pycares.errno.ARES_ENOMEM):
            self.errorno = pycares.errno.ARES_EBADNAME
        self.assertEqual(self.errorno, pycares.errno.ARES_EBADNAME)
        self.assertEqual(self.result, None)
        # use it as is (it's IDNA encoded internally)
        self.channel.query(host, pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_a_result)
            self.assertNotEqual(r.host, None)

    def test_idna2008_encoding(self):
        try:
            import idna
        except ImportError:
            raise unittest.SkipTest('idna module not installed')
        host = 'straße.de'
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.gethostbyname(host, socket.AF_INET, cb)
        self.wait()
        self.assertNoError(self.errorno)
        self.assertEqual(type(self.result), pycares.ares_host_result)
        self.assertTrue('81.169.145.78' in self.result.addresses)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    @unittest.skipIf(sys.platform == 'darwin', 'skipped on MacOS since resolver may work even if resolv.conf is broken')
    def test_custom_resolvconf(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(tries=1, timeout=2.0, resolvconf_path=os.path.join(FIXTURES_PATH, 'badresolv.conf'))
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.result, None)
        # TODO: some runners fail with ARES_ECONNREFUSED, which may make sense...
        #self.assertEqual(self.errorno, pycares.errno.ARES_ETIMEOUT)

    def test_errorcode_dict(self):
        for err in ('ARES_SUCCESS', 'ARES_ENODATA', 'ARES_ECANCELLED'):
            val = getattr(pycares.errno, err)
            self.assertEqual(pycares.errno.errorcode[val], err)

    def test_search(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(timeout=5.0, tries=1, domains=['google.com'])
        self.channel.search('cloud', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_a_result)
            self.assertNotEqual(r.host, None)

    def test_lookup(self):
        channel = pycares.Channel(
            lookups="b",
            timeout=1,
            tries=1,
            socket_receive_buffer_size=4096,
            servers=["8.8.8.8", "8.8.4.4"],
            tcp_port=53,
            udp_port=53,
            rotate=True,
        )

        def on_result(result, errorno):
            self.result, self.errorno = result, errorno

        for domain in [
            "google.com",
            "microsoft.com",
            "apple.com",
            "amazon.com",
            "baidu.com",
            "alipay.com",
            "tencent.com",
        ]:
            self.result, self.errorno = None, None
            self.channel.query(domain, pycares.QUERY_TYPE_A, on_result)
            self.wait()
            self.assertNoError(self.errorno)
            self.assertTrue(self.result is not None and len(self.result) > 0)
            for r in self.result:
                self.assertEqual(type(r), pycares.ares_query_a_result)
                self.assertNotEqual(r.host, None)
                self.assertTrue(r.type == 'A')

    def test_strerror_str(self):
        for key in pycares.errno.errorcode:
            self.assertTrue(type(pycares.errno.strerror(key)), str)


class ChannelCloseTest(unittest.TestCase):

    def test_close_from_same_thread(self):
        # Test that close() works when called from the same thread
        channel = pycares.Channel()

        # Start a query
        result = []
        def cb(res, err):
            result.append((res, err))

        channel.query('google.com', pycares.QUERY_TYPE_A, cb)

        # Close should work fine from same thread
        channel.close()

        # Channel should be closed, no more operations allowed
        with self.assertRaises(Exception):
            channel.query('google.com', pycares.QUERY_TYPE_A, cb)

    def test_close_from_different_thread_safe(self):
        # Test that close() can be safely called from different thread
        channel = pycares.Channel()
        close_complete = threading.Event()

        def close_in_thread():
            channel.close()
            close_complete.set()

        thread = threading.Thread(target=close_in_thread)
        thread.start()
        thread.join()

        # Should complete without errors
        self.assertTrue(close_complete.is_set())
        # Channel should be destroyed
        self.assertIsNone(channel._channel)

    def test_close_idempotent(self):
        # Test that close() can be called multiple times
        channel = pycares.Channel()
        channel.close()
        channel.close()  # Should not raise

    def test_threadsafe_close(self):
        # Test that close() can be called from any thread
        channel = pycares.Channel()
        close_complete = threading.Event()

        # Close from another thread
        def close_in_thread():
            channel.close()
            close_complete.set()

        thread = threading.Thread(target=close_in_thread)
        thread.start()
        thread.join()

        self.assertTrue(close_complete.is_set())
        self.assertIsNone(channel._channel)

    def test_threadsafe_close_with_pending_queries(self):
        # Test close with queries in flight
        channel = pycares.Channel()
        query_completed = threading.Event()
        cancelled_count = 0

        def cb(result, error):
            nonlocal cancelled_count
            if error == pycares.errno.ARES_ECANCELLED:
                cancelled_count += 1
            if cancelled_count >= 3:  # All queries cancelled
                query_completed.set()

        # Start several queries
        channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        channel.query('github.com', pycares.QUERY_TYPE_A, cb)
        channel.query('python.org', pycares.QUERY_TYPE_A, cb)

        # Close immediately - this should cancel pending queries
        channel.close()

        # Wait for cancellation callbacks
        self.assertTrue(query_completed.wait(timeout=2.0))
        self.assertEqual(cancelled_count, 3)  # All 3 queries should be cancelled

    def test_query_after_close_raises(self):
        # Test that queries raise after close()
        channel = pycares.Channel()
        channel.close()

        def cb(result, error):
            pass

        with self.assertRaises(RuntimeError) as cm:
            channel.query('example.com', pycares.QUERY_TYPE_A, cb)

        self.assertIn("destroyed", str(cm.exception))

    def test_close_from_different_thread(self):
        # Test that close works from different thread
        channel = pycares.Channel()
        close_complete = threading.Event()

        def close_in_thread():
            channel.close()
            close_complete.set()

        thread = threading.Thread(target=close_in_thread)
        thread.start()
        thread.join()

        self.assertTrue(close_complete.is_set())
        self.assertIsNone(channel._channel)

    def test_automatic_cleanup_same_thread(self):
        # Test that __del__ cleans up automatically when in same thread
        # Create a channel and weak reference to track its lifecycle
        channel = pycares.Channel()
        weak_ref = weakref.ref(channel)

        # Verify channel exists
        self.assertIsNotNone(weak_ref())

        # Delete the channel reference
        del channel

        # Force garbage collection
        gc.collect()
        gc.collect()  # Sometimes needs multiple passes

        # Channel should be gone now (cleaned up by __del__)
        self.assertIsNone(weak_ref())

    def test_automatic_cleanup_different_thread_with_shutdown_thread(self):
        # Test that __del__ now safely cleans up using shutdown thread
        # when channel is deleted from a different thread
        channel_container = []
        weak_ref_container = []

        def create_channel_in_thread():
            channel = pycares.Channel()
            weak_ref = weakref.ref(channel)
            channel_container.append(channel)
            weak_ref_container.append(weak_ref)

        # Create channel in different thread
        thread = threading.Thread(target=create_channel_in_thread)
        thread.start()
        thread.join()

        # Get the weak reference
        weak_ref = weak_ref_container[0]

        # Verify channel exists
        self.assertIsNotNone(weak_ref())

        # Delete the channel reference from main thread
        channel_container.clear()

        # Force garbage collection
        gc.collect()
        gc.collect()

        # Give the shutdown thread time to run
        time.sleep(0.1)

        # Channel should be cleaned up via the shutdown thread
        self.assertIsNone(weak_ref())

        # Note: The shutdown thread mechanism ensures safe cleanup
        # even when deleted from a different thread

    def test_no_crash_on_interpreter_shutdown(self):
        # Test that channels with pending queries don't crash during interpreter shutdown
        import subprocess

        # Path to the shutdown test script
        script_path = os.path.join(os.path.dirname(__file__), 'shutdown_at_exit_script.py')

        # Run the script in a subprocess
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )

        # Should exit cleanly without errors
        self.assertEqual(result.returncode, 0)
        # Should not have PythonFinalizationError in stderr
        self.assertNotIn('PythonFinalizationError', result.stderr)
        self.assertNotIn('can\'t create new thread at interpreter shutdown', result.stderr)

    def test_context_manager(self):
        # Test that Channel works as a context manager
        result_container = []

        def cb(result, error):
            result_container.append((result, error))

        # Test normal usage
        with pycares.Channel() as channel:
            self.assertIsNotNone(channel._channel)
            # Can make queries while in context
            channel.query('example.com', pycares.QUERY_TYPE_A, cb)

        # Channel should be destroyed after exiting context
        self.assertIsNone(channel._channel)

        # Test with exception
        try:
            with pycares.Channel() as channel2:
                self.assertIsNotNone(channel2._channel)
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Channel should still be destroyed even with exception
        self.assertIsNone(channel2._channel)

    def test_concurrent_close_multiple_channels(self):
        # Test multiple channels being closed concurrently
        channels = []
        for _ in range(10):
            channels.append(pycares.Channel())

        close_events = []
        threads = []

        def close_channel(ch, event):
            ch.close()
            event.set()

        # Start threads to close all channels concurrently
        for ch in channels:
            event = threading.Event()
            close_events.append(event)
            thread = threading.Thread(target=close_channel, args=(ch, event))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all channels were closed
        for event in close_events:
            self.assertTrue(event.is_set())

        for ch in channels:
            self.assertTrue(ch._channel is None)

    def test_rapid_channel_creation_and_close(self):
        # Test rapid creation and closing of channels
        for i in range(20):
            channel = pycares.Channel()

            # Alternate between same-thread and cross-thread closes
            if i % 2 == 0:
                channel.close()
            else:
                def close_in_thread(channel):
                    channel.close()

                thread = threading.Thread(target=functools.partial(close_in_thread, channel))
                thread.start()
                thread.join()

            # Verify channel is closed
            self.assertTrue(channel._channel is None)

    def test_close_with_active_queries_from_different_thread(self):
        # Test closing a channel with active queries from a different thread
        channel = pycares.Channel()
        query_started = threading.Event()
        query_cancelled = threading.Event()

        def query_cb(result, error):
            if error == pycares.errno.ARES_ECANCELLED:
                query_cancelled.set()

        # Start queries in one thread
        def start_queries():
            # Use a non-responsive server to ensure queries stay pending
            channel.servers = ['192.0.2.1']  # TEST-NET-1, should not respond
            for i in range(5):
                channel.query(f'test{i}.example.com', pycares.QUERY_TYPE_A, query_cb)
            query_started.set()

        query_thread = threading.Thread(target=start_queries)
        query_thread.start()

        # Wait for queries to start
        self.assertTrue(query_started.wait(timeout=2.0))

        # Close from main thread
        channel.close()

        # Verify channel is closed
        self.assertTrue(channel._channel is None)

        query_thread.join()

    def test_multiple_closes_from_different_threads(self):
        # Test that multiple threads can call close() safely
        channel = pycares.Channel()
        close_count = 0
        close_lock = threading.Lock()

        def close_and_count():
            channel.close()
            with close_lock:
                nonlocal close_count
                close_count += 1

        # Start multiple threads trying to close the same channel
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=close_and_count)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All threads should complete successfully
        self.assertEqual(close_count, 5)
        self.assertTrue(channel._channel is None)


class EventThreadTest(unittest.TestCase):

    def setUp(self):
        self.channel = pycares.Channel(timeout=10.0, tries=1, servers=['8.8.8.8', '8.8.4.4'], event_thread=True)
        self.is_ci = os.environ.get('APPVEYOR') or os.environ.get('TRAVIS') or os.environ.get('GITHUB_ACTION')

    def tearDown(self):
        self.channel = None

    def assertNoError(self, errorno):
        if errorno == pycares.errno.ARES_ETIMEOUT and self.is_ci:
            raise unittest.SkipTest('timeout')
        self.assertEqual(errorno, None)

    def test_query_a(self):
        self.result, self.errorno = None, None
        event = threading.Event()
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
            event.set()
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        event.wait()
        self.assertNoError(self.errorno)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_a_result)
            self.assertNotEqual(r.host, None)

if __name__ == '__main__':
    unittest.main(verbosity=2)

