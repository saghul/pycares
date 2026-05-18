"""Regression test: Channel.close() racing with Channel.query().

We race query() against close() in two threads. Without the fixes
this reproduces both:

  * a TypeError when self._channel goes None between the check and
    self._channel[0], and
  * a use-after-free where ares_destroy ran underneath the in-flight
    submission (visible as ARES_ENOSERVER from query()).

The test is skipped by default because it deliberately hammers the
scheduler for a few seconds; opt in with PYCARES_RUN_RACE_TESTS=1.
"""
import os
import threading
import time
import unittest

import pycares


@unittest.skipUnless(
    os.environ.get('PYCARES_RUN_RACE_TESTS'),
    "Set PYCARES_RUN_RACE_TESTS=1 to run scheduler-stress race tests",
)
class CloseQueryRaceTest(unittest.TestCase):
    def test_close_during_query_does_not_crash(self):
        rounds = 10000
        crashes = []

        def _cb(result, error):
            pass

        def round_once(i):
            ch = pycares.Channel(timeout=1.0, tries=1,
                                 servers=['8.8.8.8', '1.1.1.1'])
            barrier = threading.Barrier(2)

            def query_thread():
                barrier.wait()
                for j in range(20):
                    try:
                        ch.query('race-%d-%d.example.invalid' % (i, j),
                                 pycares.QUERY_TYPE_A, callback=_cb)
                    except RuntimeError:
                        return
                    except Exception as e:
                        crashes.append((i, j, repr(e)))
                        return

            def close_thread():
                barrier.wait()
                time.sleep(0.003)
                ch.close()

            tc = threading.Thread(target=close_thread)
            tq = threading.Thread(target=query_thread)
            tc.start()
            tq.start()
            tc.join(timeout=10)
            tq.join(timeout=10)

        for i in range(rounds):
            round_once(i)
            if len(crashes) >= 5:
                break

        # Allow callbacks fired by ares_cancel to drain.
        time.sleep(2)

        self.assertFalse(
            crashes,
            "unexpected exceptions during close/query race: %r" % (crashes,),
        )
