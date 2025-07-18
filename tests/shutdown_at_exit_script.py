#!/usr/bin/env python3
"""Script to test that shutdown thread handles interpreter shutdown gracefully."""

import sys

import pycares

# Create a channel
channel = pycares.Channel()


# Start a query to ensure pending handles
def callback(result, error):
    pass


channel.query("example.com", pycares.QUERY_TYPE_A, callback)

# Exit immediately - the channel will be garbage collected during interpreter shutdown
# This should not raise PythonFinalizationError
sys.exit(0)
