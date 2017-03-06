from __future__ import absolute_import, division, print_function

from .baseDescriptor import *


class Density(BaseDescriptor):
    def __init__(self, ignoredTags=None, includedTags=None):
        BaseDescriptor.__init__(self)
        self.ignoredTags = ignoredTags or ["silence"]
        self.includedTags = includedTags

    def configure(self, paramDict):
        """Configure current descriptor mapping dict to parameters"""
        raise NotImplementedError("Not Implemented.")

    def getDescriptorForPattern(self, pattern):
        density = 0
        _checkedPattern = pattern.getPatternWithoutTags(tagToLookFor=self.ignoredTags)
        if self.includedTags:
            _checkedPattern = _checkedPattern.getPatternWithTags(tagToLookFor=self.includedTags, makeCopy=False)
        for e in _checkedPattern.events:
            density += e.duration
        return density
