#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

import os
import sys

if __name__ == '__main__':
    sys.path.insert(1, os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir)))
    from test_pattern_utils import *  # enteiendo que esto debería importar el módulo instalado.
else:
    from .test_pattern_utils import *

from gsapi import *


class AgnosticDensityTest(GSTestBase):
    def generateCachedDataset(self):
        return GSDataset(midiGlob="funkyfresh.mid",
                         midiFolder=self.getLocalCorpusPath('drums'),
                         midiMap=GSPatternUtils.simpleDrumMap,
                         checkForOverlapped=True)

    def test_AgnosticDensity_simple(self):
        numSteps = 32
        agnosticDensity = GSPatternTransformers.AgnosticDensity(numSteps=numSteps)
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
