#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function


class BaseDescriptor(object):
    def __init__(self):
        self.type = "descriptor"

    def configure(self, paramDict):
        """
        Configure the current descriptor mapping dict to parameters.

        """
        raise NotImplementedError("Not Implemented.")

    def getDescriptorForPattern(self, pattern):
        """
        Compute a unique value for a given pattern.
        It can be a sliced part of a bigger one.

        """
        raise NotImplementedError("Not Implemented.")

