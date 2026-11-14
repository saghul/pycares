import gc
import threading
import unittest
import weakref
from unittest.mock import patch

import pycares


class ShutdownCallbackRetentionTest(unittest.TestCase):
    def setUp(self):
        self.worker_idle = threading.Event()
        self.manager = pycares._shutdown_manager
        self.original_queue = self.manager._queue

        class ObservableQueue:
            def get(inner_self):
                # The worker reaches get() only after releasing its prior locals.
                if self.original_queue.empty():
                    self.worker_idle.set()
                return self.original_queue.get()

            def put(inner_self, item):
                self.original_queue.put(item)

        self.manager._queue = ObservableQueue()
        self.addCleanup(setattr, self.manager, "_queue", self.original_queue)

    def _assert_released_after_worker_idle(self, released):
        self.assertTrue(self.worker_idle.wait(2), "shutdown worker did not become idle")
        gc.collect()
        self.assertTrue(released.is_set(), "callback owner remained retained after native destruction")

    def test_callback_owner_is_retained_during_native_destruction(self):
        destroy_started = threading.Event()
        allow_destroy_to_finish = threading.Event()
        released = threading.Event()

        class Owner:
            def sock_state_cb(self, socket_fd, readable, writable):
                pass

        owner = Owner()
        owner_ref = weakref.ref(owner, lambda _: released.set())
        channel = pycares.Channel(sock_state_cb=owner.sock_state_cb)
        native_channel = channel._channel[0]
        native_lib = pycares._lib

        class BlockingNativeLib:
            def __getattr__(self, name):
                return getattr(native_lib, name)

            def ares_destroy(self, native_channel_arg):
                if native_channel_arg == native_channel:
                    destroy_started.set()
                    allow_destroy_to_finish.wait()
                native_lib.ares_destroy(native_channel_arg)

        try:
            with patch.object(pycares, "_lib", BlockingNativeLib()):
                channel.close()
                del channel, owner
                self.assertTrue(destroy_started.wait(2), "native destruction did not start")
                self.worker_idle.clear()
                gc.collect()
                self.assertIsNotNone(owner_ref(), "callback owner was released during native destruction")
        finally:
            allow_destroy_to_finish.set()

        self._assert_released_after_worker_idle(released)
        self.assertIsNone(owner_ref())

    def test_close_releases_final_socket_callback_owner(self):
        released = threading.Event()

        class Owner:
            def sock_state_cb(self, socket_fd, readable, writable):
                pass

        owner = Owner()
        owner_ref = weakref.ref(owner, lambda _: released.set())
        channel = pycares.Channel(sock_state_cb=owner.sock_state_cb)
        native_channel = channel._channel[0]
        native_lib = pycares._lib
        destroy_finished = threading.Event()

        class MonitoringNativeLib:
            def __getattr__(lib_proxy, name):
                return getattr(native_lib, name)

            def ares_destroy(lib_proxy, native_channel_arg):
                native_lib.ares_destroy(native_channel_arg)
                if native_channel_arg == native_channel:
                    self.worker_idle.clear()
                    destroy_finished.set()

        with patch.object(pycares, "_lib", MonitoringNativeLib()):
            channel.close()
            del channel, owner
            self.assertTrue(destroy_finished.wait(2), "native destruction did not finish")
            self._assert_released_after_worker_idle(released)

        self.assertIsNone(owner_ref())


if __name__ == '__main__':
    unittest.main(verbosity=2)
