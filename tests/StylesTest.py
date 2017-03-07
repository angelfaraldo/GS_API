from __future__ import absolute_import, division, print_function

import os
import sys

if __name__ == '__main__':
    sys.path.insert(1, os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir)))
    from .PatternTestUtils import *
    from python.gsapi.utils.pitchSpelling import *
    from python.gsapi.patterns.utils import *
else:
    from .PatternTestUtils import *
    from python.gsapi.utils.pitchSpelling import *
    from python.gsapi.patterns.utils import *
from gsapi import *


class GSStylesTest(GSTestBase):

    def generateCachedDataset(self):
      return GSDataset(midiGlob="*.mid",
                       midiFolder=self.getLocalCorpusPath('harmony'),
                       midiMap="pitchNames",
                       checkForOverlapped=True)

    def testGSMarkovStyleSimple(self):
      loopDuration=4
      markov = GSStyles.GSMarkovStyle(order = 1,numSteps=32,loopDuration=loopDuration)
      pList = self.cachedDataset.getAllSliceOfDuration(loopDuration);
      markov.generateStyle(pList)
      self.checkPatternValid(markov.generatePattern())


    def testMarkovFromViewpointChords(self):
      loopDuration=32
      pList = self.cachedDataset.getAllSliceOfDuration(loopDuration);

      markov = GSStyles.GSMarkovStyle(order = 1,numSteps=4,loopDuration=loopDuration)

      cList = list(map(lambda x:x.generateViewpoint("chords",GSDescriptors.GSDescriptorChord(),sliceType = 4),pList))
      # for p in cList:
      #   for e in p:
      #     e.tag = str(e.tag[0])+str(e.tag[1])
      markov.generateStyle(cList)
      # print (markov.markovChain)

      chordPattern  =markov.generatePattern()

      # print (chordPattern)
      self.checkPatternValid(chordPattern)


      midiPattern = GSPattern()
      chordSuccession = []
      for e in chordPattern:
        chordSuccession+=[str("".join(e.tag))]
        chroma = defaultPitchNames.index(e.tag[0])
        notes = chordTypes[e.tag[1]]
        for n in notes:
          midiPattern.events+=[GSPatternEvent(pitch = 48+chroma+n,startTime=e.startTime,duration=e.duration,velocity=100)]

      midiPattern.name = '-'.join(chordSuccession)
      print(chordSuccession)
      midiPattern.setDurationFromLastEvent()
      print(chordPattern)
      print(midiPattern)
      GSIO.toMidi(midiPattern,folderPath="../../sandbox/chordGen",name="tests")





if __name__ == '__main__':

    runTest(profile=False, getStat=False)

