#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from .base_descriptor import BaseDescriptor


class NumberOfTags(BaseDescriptor):
    """
    Calculates the number of tags in a given Pattern.

    """

    def __init__(self, ignoredTags=None, includedTags=None):
        BaseDescriptor.__init__(self)
        self.ignoredTags = ignoredTags or ["silence"]
        self.includedTags = includedTags

    def configure(self, paramDict):
        """
        Configure current descriptor mapping dict to parameters.

        """
        raise NotImplementedError("Not Implemented.")

    def getDescriptorForPattern(self, pattern):
        _checkedPattern = pattern.getPatternWithoutTags(tagToLookFor=self.ignoredTags)
        if self.includedTags:
            _checkedPattern = _checkedPattern.getPatternWithTags(tagToLookFor=self.includedTags, makeCopy=False)
        return len(_checkedPattern.getAllTags())
