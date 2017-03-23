#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from .test_utils import *


class GSStylesTest(GSTestBase):
    def generateCachedDataset(self):
        return gsdataset.Dataset(midiGlob="*.mid", midiFolder=self.getLocalCorpusPath('harmony'),
                                 midiMap="pitchName", checkForOverlapped=True)

    def testGSMarkovStyleSimple(self):
        loopDuration = 4
        markov = gsstyles.MarkovStyle(order=1, numSteps=32, loopDuration=loopDuration)
        pList = self.cachedDataset.getAllSliceOfDuration(loopDuration)
        markov.generateStyle(pList)
        self.checkPatternValid(markov.generatePattern())

    def testMarkovFromViewpointChords(self):
        loopDuration = 32
        pList = self.cachedDataset.getAllSliceOfDuration(loopDuration)
        markov = gsstyles.MarkovStyle(order=1, numSteps=4, loopDuration=loopDuration)
        cList = list(map(lambda x: x.generateViewpoint("chords", gsdescriptors.Chord(), sliceType=4), pList))
        markov.generateStyle(cList)
        chordPattern = markov.generatePattern()
        self.checkPatternValid(chordPattern)
        midiPattern = gspattern.Pattern()
        chordSequence = []
        for e in chordPattern:
            chordSequence += [str("".join(e.tag))]
            chroma = gsdefs.defaultPitchNames.index(e.tag[0])
            notes = gsdefs.chordTypes[e.tag[1]]
            for n in notes:
                midiPattern.events += [gspattern.Event(pitch=48 + chroma + n, startTime=e.startTime,
                                                       duration=e.duration, velocity=100)]
        midiPattern.name = '-'.join(chordSequence)
        print(chordSequence)
        midiPattern.durationToLastEvent()
        print(chordPattern)
        print(midiPattern)
        gsio.toMidiFile(midiPattern, folderPath="../output/chordGen", name="tests")


if __name__ == '__main__':
    runTest(profile=False, getStat=False)
