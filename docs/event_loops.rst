.. _event_loops:

======================
Event loop integration
======================


pycares can be integrated in an already existing event loop without much trouble.
The examples folder contains several examples:

* cares-select.py: integration with plain select
* cares-poll.py: integration with plain poll
* cares-selectors.py: integration with the builtin selectors module
* cares-resolver.py: integration with the pyuv event loop
* cares-asyncio.py: integration with the asyncio framework

Additionally, `Tornado <http://tornadoweb.org>`_ provides integration
with pycaes through a `resolver module <https://github.com/facebook/tornado/blob/master/tornado/platform/caresresolver.py>`_.

