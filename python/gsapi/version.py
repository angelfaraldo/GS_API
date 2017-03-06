from __future__ import absolute_import, division, print_function

# this is the full version name
# changing it will change version when uploading to pip and in the documentation
gsapiFullVersion = u'1.0.4'


def getGsapiFullVersion():
    """Helper to get full version name"""
    return gsapiFullVersion


def getGsapiShortVersion():
    """Helper to get only first two elements of full version name"""
    return u'.'.join(gsapiFullVersion.split('.')[:2])
