"""Regression tests for handle leaks in _handle_to_channel.

The submission methods register a cffi handle in the global
_handle_to_channel dict before the c-ares call runs. If argument
evaluation raises (for example parse_name() raising on an invalid IDNA
name) the handle must still be popped, otherwise it (and the Channel
reference it carries) leaks forever.
"""
import unittest

import pycares
from pycares import _handle_to_channel


def _cb(result, error):
    pass


class HandleLeakTest(unittest.TestCase):
    def setUp(self):
        self.channel = pycares.Channel(
            timeout=1.0, tries=1, servers=['8.8.8.8'],
        )

    def tearDown(self):
        self.channel.close()

    def test_query_does_not_leak_on_parse_name_failure(self):
        before = len(_handle_to_channel)
        with self.assertRaises(UnicodeError):
            self.channel.query(
                '\udc80bad', pycares.QUERY_TYPE_A, callback=_cb,
            )
        self.assertEqual(len(_handle_to_channel), before)

    def test_search_does_not_leak_on_parse_name_failure(self):
        before = len(_handle_to_channel)
        with self.assertRaises(UnicodeError):
            self.channel.search(
                '\udc80bad', pycares.QUERY_TYPE_A, callback=_cb,
            )
        self.assertEqual(len(_handle_to_channel), before)

    def test_getaddrinfo_does_not_leak_on_parse_name_failure(self):
        before = len(_handle_to_channel)
        with self.assertRaises(UnicodeError):
            self.channel.getaddrinfo('\udc80bad', None, callback=_cb)
        self.assertEqual(len(_handle_to_channel), before)

    def test_gethostbyaddr_does_not_leak_on_invalid_ip(self):
        before = len(_handle_to_channel)
        with self.assertRaises(ValueError):
            self.channel.gethostbyaddr('not-an-ip', callback=_cb)
        self.assertEqual(len(_handle_to_channel), before)

    def test_getnameinfo_does_not_leak_on_invalid_ip(self):
        before = len(_handle_to_channel)
        with self.assertRaises(ValueError):
            self.channel.getnameinfo(('not-an-ip', 80), 0, callback=_cb)
        self.assertEqual(len(_handle_to_channel), before)

    def test_search_does_not_leak_dnsrec_on_closed_channel(self):
        # Regression test: search() builds its own ares_dns_record_t before
        # acquiring the channel. If the channel is already closed,
        # _capture_channel() raises before that record is ever handed off
        # to a callback, so search() must free it itself instead of leaking
        # the native allocation.
        self.channel.close()
        before = len(_handle_to_channel)
        with self.assertRaises(RuntimeError):
            self.channel.search('example.com', pycares.QUERY_TYPE_A, callback=_cb)
        self.assertEqual(len(_handle_to_channel), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
