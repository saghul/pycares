import asyncio
import socket
from typing import Any, Callable, Optional

import pycares


class DNSResolver:
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        # Use event_thread=True for automatic event handling in a separate thread
        self._channel = pycares.Channel(event_thread=True)
        self.loop = loop or asyncio.get_running_loop()

    def query(
        self, name: str, query_type: int, cb: Callable[[Any, Optional[int]], None]
    ) -> None:
        self._channel.query(name, query_type, cb)

    def gethostbyname(
        self, name: str, cb: Callable[[Any, Optional[int]], None]
    ) -> None:
        self._channel.gethostbyname(name, socket.AF_INET, cb)

    def close(self) -> None:
        """Thread-safe shutdown of the channel."""
        # Simply call close() - it's thread-safe and handles everything
        self._channel.close()


async def main() -> None:
    # Track queries
    query_count = 0
    completed_count = 0
    cancelled_count = 0

    def cb(query_name: str) -> Callable[[Any, Optional[int]], None]:
        def _cb(result: Any, error: Optional[int]) -> None:
            nonlocal completed_count, cancelled_count
            if error == pycares.errno.ARES_ECANCELLED:
                cancelled_count += 1
                print(f"Query for {query_name} was CANCELLED")
            else:
                completed_count += 1
                print(
                    f"Query for {query_name} completed - Result: {result}, Error: {error}"
                )

        return _cb

    loop = asyncio.get_running_loop()
    resolver = DNSResolver(loop)

    print("=== Starting first batch of queries ===")
    # First batch - these should complete
    resolver.query("google.com", pycares.QUERY_TYPE_A, cb("google.com"))
    resolver.query("cloudflare.com", pycares.QUERY_TYPE_A, cb("cloudflare.com"))
    query_count += 2

    # Give them a moment to complete
    await asyncio.sleep(0.5)

    print("\n=== Starting second batch of queries (will be cancelled) ===")
    # Second batch - these will be cancelled
    resolver.query("github.com", pycares.QUERY_TYPE_A, cb("github.com"))
    resolver.query("stackoverflow.com", pycares.QUERY_TYPE_A, cb("stackoverflow.com"))
    resolver.gethostbyname("python.org", cb("python.org"))
    query_count += 3

    # Immediately close - this will cancel pending queries
    print("\n=== Closing resolver (cancelling pending queries) ===")
    resolver.close()
    print("Resolver closed successfully")

    print(f"\n=== Summary ===")
    print(f"Total queries: {query_count}")
    print(f"Completed: {completed_count}")
    print(f"Cancelled: {cancelled_count}")


if __name__ == "__main__":
    # Check if c-ares supports threads
    if pycares.ares_threadsafety():
        # For Python 3.7+
        asyncio.run(main())
    else:
        print("c-ares was not compiled with thread support")
        print("Please see examples/cares-asyncio.py for sock_state_cb usage")
