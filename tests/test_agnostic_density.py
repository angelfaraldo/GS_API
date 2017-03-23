#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from .test_utils import *


class AgnosticDensityTest(GSTestBase):
    def generateCachedDataset(self):
        return gsdataset.Dataset(midiGlob="funkyfresh.mid", midiFolder=self.getLocalCorpusPath('drums'),
                                 midiMap=gsdefs.simpleDrumMap, checkForOverlapped=True)

    def test_AgnosticDensity_simple(self):
        numSteps = 32
        agnosticDensity = gstransformers.AgnosticDensity(numSteps=numSteps)
        for p in self.cachedDataset:
            shortPatterns = p.splitInEqualLengthPatterns(4, makeCopy=False)
            for shortPattern in shortPatterns:
                testLog.info('checking pattern' + shortPattern.name)
                randomDensity = {}
                for t in shortPattern.getAllTags():
                    randomDensity[t] = random.random() * 2.0
                newP = agnosticDensity.transformPattern(shortPattern, {'normalizedDensities': randomDensity})
                self.checkPatternValid(newP)


if __name__ == '__main__':
    runTest(profile=True, getStat=False)
