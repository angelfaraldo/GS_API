# !/usr/bin/env python
# encoding: utf-8

"""
The GS-API version number.
"""

from __future__ import absolute_import, division, print_function

# Library's full version name.
# Changing it will change the version in pip and in the documentation.
GSAPI_FULL_VERSION = u'1.0.5'


def getGsapiFullVersion():
    """
    Helper to get the full version name.

    """
    return GSAPI_FULL_VERSION


def getGsapiShortVersion():
    """
    Helper to get the short version name.

    """
    return u'.'.join(GSAPI_FULL_VERSION.split('.')[:2])
