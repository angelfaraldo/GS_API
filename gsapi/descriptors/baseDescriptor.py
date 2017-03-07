from __future__ import absolute_import, division, print_function
import logging


class BaseDescriptor(object):
    def __init__(self):
        pass

    def getDescriptorForPattern(self, pattern):
        """Compute a unique value for a given pattern, which can be a sliced part of a bigger one."""
        raise NotImplementedError("Not Implemented.")

    def configure(self, paramDict):
        """Configure current descriptor mapping dict to parameters"""
        raise NotImplementedError("Not Implemented.")
