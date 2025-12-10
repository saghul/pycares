#!/usr/bin/env python3
"""Script to test that shutdown thread handles interpreter shutdown gracefully."""

import sys

import pycares


def dummy(*args):
    pass


# Create a channel
# TODO: using event thread seems to crash on Windows 11 ARM.
channel = pycares.Channel(sock_state_cb=dummy)


# Start a query to ensure pending handles
def callback(result, error):
    pass


channel.query("example.com", pycares.QUERY_TYPE_A, callback=callback)

# Exit immediately - the channel will be garbage collected during interpreter shutdown
# This should not raise PythonFinalizationError
sys.exit(0)
