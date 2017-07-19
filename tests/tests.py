#!/usr/bin/env python

import select
import socket
import sys
import unittest

import pycares


class DNSTest(unittest.TestCase):

    def setUp(self):
        self.channel = pycares.Channel(timeout=5.0, tries=1)

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

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyaddr(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.gethostbyaddr('127.0.0.1', cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyaddr6(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.gethostbyaddr('::1', cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyname(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.gethostbyname('localhost', socket.AF_INET, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_gethostbyname_small_timeout(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(timeout=0.5, tries=1)
        self.channel.gethostbyname('localhost', socket.AF_INET, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        self.assertEqual(type(self.result), pycares.ares_host_result)

    @unittest.skipIf(sys.platform == 'win32', 'skipped on Windows')
    def test_getnameinfo(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.getnameinfo(('127.0.0.1', 80), pycares.ARES_NI_LOOKUPHOST|pycares.ARES_NI_LOOKUPSERVICE, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        self.assertEqual(type(self.result), pycares.ares_nameinfo_result)
        self.assertIn(self.result.node, ('localhost.localdomain', 'localhost'))
        self.assertEqual(self.result.service, 'http')

    def test_query_a(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_simple_result)
            self.assertNotEqual(r.host, None)
            self.assertTrue(r.ttl >= 0)

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
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_simple_result)
            self.assertNotEqual(r.host, None)
            self.assertTrue(r.ttl >= 0)

    def test_query_cname(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('www.amazon.com', pycares.QUERY_TYPE_CNAME, cb)
        self.wait()
        self.assertEqual(type(self.result), pycares.ares_query_cname_result)
        self.assertEqual(self.errorno, None)

    def test_query_mx(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_MX, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_mx_result)
            self.assertTrue(r.ttl >= 0)

    def test_query_ns(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_NS, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_ns_result)

    def test_query_txt(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_txt_result)
            self.assertTrue(r.ttl >= 0)

    def test_query_txt_chunked(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('jobscoutdaily.com', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        # If the chunks are aggregated, only one TXT record should be visible. Three would show if they are not properly merged.
        # jobscoutdaily.com.    21600   IN  TXT "v=spf1 " "include:emailcampaigns.net include:spf.dynect.net  include:ccsend.com include:_spf.elasticemail.com ip4:67.200.116.86 ip4:67.200.116.90 ip4:67.200.116.97 ip4:67.200.116.111 ip4:74.199.198.2 " " ~all"
        self.assertEqual(len(self.result), 1)
        self.assertEqual(self.result[0].text, b'v=spf1 include:emailcampaigns.net include:spf.dynect.net  include:ccsend.com include:_spf.elasticemail.com ip4:67.200.116.86 ip4:67.200.116.90 ip4:67.200.116.97 ip4:67.200.116.111 ip4:74.199.198.2  ~all')

    def test_query_txt_multiple_chunked(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('s-pulse.co.jp', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        # s-pulse.co.jp.      3600    IN  TXT "MS=ms18955624"
        # s-pulse.co.jp.      3600    IN  TXT "v=spf1 " "include:spf-bma.mpme.jp ip4:202.248.11.9 ip4:202.248.11.10 " "ip4:218.223.68.132 ip4:218.223.68.77 ip4:210.254.139.121 " "ip4:211.128.73.121 ip4:210.254.139.122 ip4:211.128.73.122 " "ip4:210.254.139.123 ip4:211.128.73.123 ip4:210.254.139.124 " "ip4:211.128.73.124 ip4:210.254.139.13 ip4:211.128.73.13 " "ip4:52.68.199.198 include:spf.betrend.com " "include:spf.protection.outlook.com " "~all"
        self.assertEqual(len(self.result), 2)

    def test_query_txt_bytes1(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('like.com.sa', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_txt_result)
            self.assertIsInstance(r.text, bytes)
            self.assertTrue(r.ttl >= 0)

    def test_query_txt_bytes2(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('wide.com.es', pycares.QUERY_TYPE_TXT, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_txt_result)
            self.assertIsInstance(r.text, bytes)
            self.assertTrue(r.ttl >= 0)

    def test_query_soa(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_SOA, cb)
        self.wait()
        self.assertEqual(type(self.result), pycares.ares_query_soa_result)
        self.assertEqual(self.errorno, None)
        self.assertTrue(self.result.ttl >= 0)

    def test_query_srv(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('_xmpp-server._tcp.google.com', pycares.QUERY_TYPE_SRV, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_srv_result)
            self.assertTrue(r.ttl >= 0)

    def test_query_naptr(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('sip2sip.info', pycares.QUERY_TYPE_NAPTR, cb)
        self.wait()
        self.assertEqual(self.errorno, None)
        for r in self.result:
            self.assertEqual(type(r), pycares.ares_query_naptr_result)
            self.assertTrue(r.ttl >= 0)

    def test_query_ptr(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        ip = '8.8.8.8'
        self.channel.query(pycares.reverse_address(ip), pycares.QUERY_TYPE_PTR, cb)
        self.wait()
        self.assertEqual(type(self.result), pycares.ares_query_ptr_result)
        self.assertEqual(self.errorno, None)
        self.assertIsInstance(self.result.ttl, int)
        self.assertGreaterEqual(self.result.ttl, 0)
        self.assertLessEqual(self.result.ttl, 2**31-1)
        self.assertEqual(type(self.result.aliases), list)

    def test_query_ptr_ipv6(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        ip = '2001:4860:4860::8888'
        self.channel.query(pycares.reverse_address(ip), pycares.QUERY_TYPE_PTR, cb)
        self.wait()
        self.assertEqual(type(self.result), pycares.ares_query_ptr_result)
        self.assertEqual(self.errorno, None)
        self.assertIsInstance(self.result.ttl, int)
        self.assertGreaterEqual(self.result.ttl, 0)
        self.assertLessEqual(self.result.ttl, 2**31-1)
        self.assertEqual(type(self.result.aliases), list)


    def test_query_cancelled(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.query('google.com', pycares.QUERY_TYPE_NS, cb)
        self.channel.cancel()
        self.wait()
        self.assertEqual(self.result, None)
        self.assertEqual(self.errorno, pycares.errno.ARES_ECANCELLED)

    def test_channel_destroyed(self):
        self.channel.destroy()
        self.assertRaises(pycares.AresError, self.channel.gethostbyname, 'google.com', socket.AF_INET, lambda *x: None)

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

    def test_channel_nameservers(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(timeout=5.0, tries=1, servers=['8.8.8.8'])
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.errorno, None)

    def test_channel_nameservers2(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.servers = ['8.8.8.8']
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.errorno, None)

    def test_channel_local_ip(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel = pycares.Channel(timeout=5.0, tries=1, servers=['8.8.8.8'], local_ip='127.0.0.1')
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.result, None)
        self.assertEqual(self.errorno, pycares.errno.ARES_ECONNREFUSED)

    def test_channel_local_ip2(self):
        self.result, self.errorno = None, None
        def cb(result, errorno):
            self.result, self.errorno = result, errorno
        self.channel.servers = ['8.8.8.8']
        self.channel.set_local_ip('127.0.0.1')
        self.channel.query('google.com', pycares.QUERY_TYPE_A, cb)
        self.wait()
        self.assertEqual(self.result, None)
        self.assertEqual(self.errorno, pycares.errno.ARES_ECONNREFUSED)
        self.assertRaises(ValueError, self.channel.set_local_ip, 'an invalid ip')

    def test_channel_local_dev(self):
        '''
        Comments in c-ares say this only works for root, and ares ignores
        errors. So we won't test it.
        '''
        pass

    def test_reverse_address(self):
        s = '1.2.3.4'
        expected = '4.3.2.1.in-addr.arpa'
        self.assertEqual(pycares.reverse_address(s), expected)

        s = '2607:f8b0:4010:801::1013'
        expected = '3.1.0.1.0.0.0.0.0.0.0.0.0.0.0.0.1.0.8.0.0.1.0.4.0.b.8.f.7.0.6.2.ip6.arpa'
        self.assertEqual(pycares.reverse_address(s), expected)

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


if __name__ == '__main__':
    unittest.main(verbosity=2)

