#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from .test_utils import *


class GSPatternTest(GSTestBase):
    def generateCachedDataset(self):
        return gsdataset.Dataset(midiGlob="funkyfresh.mid", midiFolder=self.getLocalCorpusPath('drums'),
                                 midiMap="pitchName", checkForOverlapped=True)

    def test_Import(self):
        for p in self.cachedDataset.patterns:
            self.assertTrue(p is not None, 'cant import midi file %s' % p.name)
            self.assertTrue(p.duration > 0, 'cant import midi file %s: no duration' % p.name)
            self.assertTrue(p.events != [], 'cant import midi file %s: no events' % p.name)
            self.checkPatternValid(p, msg='import Pattern %s failed' % p.name)
            sliced = p.patternFromTimeSlice(0, 4)
            self.checkPatternValid(sliced, msg='slicing pattern failed')
            ps = p.splitInEqualLengthPatterns(4, makeCopy=True)
            for pp in ps:
                self.checkPatternValid(pp, msg='split in equal length failed')

    def test_Silences(self):
        for p in self.cachedDataset.patterns:
            pattern1 = p.getFilledWithSilences(perTag=True)
            pattern2 = p.getFilledWithSilences(perTag=False)
            self.checkPatternValid(pattern1, checkForDoublons=False, checkOverlap=False,
                                   msg='fill with silence per tag failed')
            self.checkPatternValid(pattern2, checkForDoublons=False, checkOverlap=False,
                                   msg='fill with silence failed')

    def test_stretch(self):
        for bp in self.cachedDataset.patterns:
            originPattern = bp.copy()
            p = bp.patternFromTimeSlice(0, 4)
            p.timeStretch(32 / 4.0)
            p.alignOnGrid(1)
            p.fillWithSilences(maxSilenceTime=1)
            p.durationToLastEvent(onlyIfBigger=False)
            self.assertTrue(p.events[-1].startTime == 31)
            self.checkPatternValid(p, msg='stretch failed \n\n%s \n\n%s' % (originPattern, p))

    def test_legato(self):
        patternList = self.cachedDataset[0].splitInEqualLengthPatterns(4, makeCopy=False)
        for p in patternList:
            p.applyLegato()
            self.checkPatternValid(p, msg='legato failed')


if __name__ == '__main__':
    runTest(profile=True, getStat=False)
