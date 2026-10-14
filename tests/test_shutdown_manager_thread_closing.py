"""Test that multiple channels can be used in parallel when the global shutdown
manager thread is stopped after each channel use
"""
import asyncio
import unittest

import pycares


class ShutdownManagerThreadClosingTest(unittest.TestCase):
    def test_shutdown_manager_thread_closing(self):

        def _cb(result, error):
            pass

        async def resolve_and_close():
            ch = pycares.Channel(timeout=1.0, tries=1, servers=['9.9.9.9'])
            # One invalid query
            ch.query('example.invalid', pycares.QUERY_TYPE_A, callback=_cb)
            # One valid query
            ch.query('google.com', pycares.QUERY_TYPE_A, callback=_cb)

            # Make sure the thread is up and running
            self.assertIsNotNone(pycares._shutdown_manager._thread)
            self.assertTrue(pycares._shutdown_manager._thread.is_alive())
            # Stop the global shutdown manager thread
            pycares._shutdown_manager.stop()
            # Make sure the thread is stopped and removed
            self.assertIsNone(pycares._shutdown_manager._thread)

        async def main():
            await asyncio.gather(*[resolve_and_close() for _ in range(10)])

        asyncio.run(main())
