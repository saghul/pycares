#!/bin/bash
# This script runs inside Docker

set -e -x


# Cleanup
cd /pycares
rm -rf wheeltmp

VERSIONS="cp35-cp35m cp36-cp36m cp37-cp37m"

# Build
for version in $VERSIONS; do
    if [[ -d /opt/python/${version} ]]; then
        /opt/python/${version}/bin/python setup.py build_ext
        /opt/python/${version}/bin/pip wheel . -w wheeltmp
    fi
done
for whl in wheeltmp/*.whl; do
    auditwheel repair $whl -w wheelhouse
done

# Cleanup
rm -rf wheeltmp
cd ..

# Test (ignore if some fail, we just want to know that the module works)
for version in $VERSIONS; do
    if [[ -d /opt/python/${version} ]]; then
        /opt/python/${version}/bin/python --version
        /opt/python/${version}/bin/pip install pycares --no-index -f /pycares/wheelhouse
        /opt/python/${version}/bin/python -c "import pycares; print('%s - %s' % (pycares.__version__, pycares.ARES_VERSION));"
    fi
done

exit 0
