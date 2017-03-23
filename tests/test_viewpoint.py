#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from .test_utils import *


class GSViewpointTest(GSTestBase):
    def generateCachedDataset(self):
        return gsdataset.Dataset(midiGlob="*.mid", midiFolder=self.getLocalCorpusPath('harmony'),
                                 midiMap="pitchName", checkForOverlapped=True)

    def test_viewpoint_defaults(self):
        for midiPattern in self.cachedDataset:
            print("\n" + midiPattern.name)
            midiPattern.generateViewpoint("chords")
            self.checkPatternValid(midiPattern, msg='chordViewPoint failed')
            for e in midiPattern.viewpoints["chords"].events:
                print(e)

    def test_viewpoint_allDescriptors_allSliceTypes(self):

        def _testAndPrint(sliceType):
            patternBeforeVP = midiPattern.copy()
            midiPattern.generateViewpoint(descriptorName, escriptor=descriptor, sliceType=sliceType)
            self.assertTrue(patternBeforeVP == midiPattern,
                            msg='viewpoint generation modified original pattern failed')
            self.checkPatternValid(midiPattern.viewpoints[descriptorName], checkOverlap=False,
                                   msg='generated viewpoint is not a valid pattern %s' %
                                       midiPattern.viewpoints[descriptorName])

        def _testDescriptor(name):
            _testAndPrint(sliceType="perEvent")
            _testAndPrint(sliceType="all")
            _testAndPrint(sliceType=1)
            _testAndPrint(sliceType=4)
            _testAndPrint(sliceType=3)

        for midiPattern in self.cachedDataset:
            for descriptorName, descriptorClass in getAllDescriptorsClasses():
                descriptor = descriptorClass()
                _testDescriptor(name=descriptorName)
            testLog.info(midiPattern.name + " ok")


if __name__ == '__main__':
    runTest(profile=False, getStat=False)
