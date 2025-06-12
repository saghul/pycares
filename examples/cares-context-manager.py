#!/usr/bin/env python
"""
Example of using pycares Channel as a context manager with event_thread=True.

This demonstrates the simplest way to use pycares with automatic cleanup.
The event thread handles all socket operations internally, and the context
manager ensures the channel is properly closed when done.
"""

import pycares
import socket
import time


def main():
    """Run DNS queries using Channel as a context manager."""
    results = []

    def callback(result, error):
        """Store results from DNS queries."""
        if error:
            print(f"Error {error}: {pycares.errno.strerror(error)}")
        else:
            print(f"Result: {result}")
        results.append((result, error))

    # Use Channel as a context manager with event_thread=True
    # This is the recommended pattern for simple use cases
    with pycares.Channel(
        servers=["8.8.8.8", "8.8.4.4"], timeout=5.0, tries=3, event_thread=True
    ) as channel:
        print("=== Making DNS queries ===")

        # Query for A records
        channel.query("google.com", pycares.QUERY_TYPE_A, callback)
        channel.query("cloudflare.com", pycares.QUERY_TYPE_A, callback)

        # Query for AAAA records
        channel.query("google.com", pycares.QUERY_TYPE_AAAA, callback)

        # Query for MX records
        channel.query("python.org", pycares.QUERY_TYPE_MX, callback)

        # Query for TXT records
        channel.query("google.com", pycares.QUERY_TYPE_TXT, callback)

        # Query using gethostbyname
        channel.gethostbyname("github.com", socket.AF_INET, callback)

        # Query using gethostbyaddr
        channel.gethostbyaddr("8.8.8.8", callback)

        print("\nWaiting for queries to complete...")
        # Give queries time to complete
        # In a real application, you would coordinate with your event loop
        time.sleep(2)

    # Channel is automatically closed when exiting the context
    print("\n=== Channel closed automatically ===")

    print(f"\nCompleted {len(results)} queries")

    # Demonstrate that the channel is closed and can't be used
    try:
        channel.query("example.com", pycares.QUERY_TYPE_A, callback)
    except RuntimeError as e:
        print(f"\nExpected error when using closed channel: {e}")


if __name__ == "__main__":
    # Check if c-ares supports threads
    if pycares.ares_threadsafety():
        print(f"Using pycares {pycares.__version__} with c-ares {pycares.ARES_VERSION}")
        print(
            f"Thread safety: {'enabled' if pycares.ares_threadsafety() else 'disabled'}\n"
        )
        main()
    else:
        print("This example requires c-ares to be compiled with thread support")
        print("Use cares-select.py or cares-asyncio.py instead")
