#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from .test_utils import *


class MarkovPatternTest(GSTestBase):
    def generateCachedDataset(self):
        return gsdataset.Dataset(midiGlob="daftpunk.mid", midiFolder=self.getLocalCorpusPath('drums'),
                                 midiMap=gsdefs.verySimpleDrumMap)

    def buildMarkov(self, order, numSteps, loopDuration):
        self.patternList = []

        for p in self.cachedDataset.patterns:
            self.patternList += p.splitInEqualLengthPatterns(loopDuration, False)
        for p in self.patternList:
            testLog.info(p)
        self.markovChain = gsstyles.PatternMarkov(order=order, numSteps=numSteps, loopDuration=loopDuration)
        self.markovChain.generateTransitionTableFromPatternList(self.patternList)
        testLog.info(self.markovChain)
        self.assertTrue(self.markovChain.isBuilt(), "markov chain has not been built.")
        self.__testMarkov(10)

    def __testMarkov(self, numPatternToTest):
        for i in range(numPatternToTest):
            pattern = self.markovChain.generatePattern()
            self.checkPatternValid(pattern, msg="markov generated a wrong patternat iteration: " + str(i))
            self.assertTrue(pattern.duration == self.markovChain.loopDuration)

    def testMarkovMatrix(self):

        def _testIt():
            self.markovChain = gsstyles.PatternMarkov(order=2, numSteps=4, loopDuration=loopDuration)
            self.markovChain.generateTransitionTableFromPatternList(self.patternList)
            tstP = self.markovChain.generatePattern()
            print(tstP)
            self.checkPatternValid(tstP)
            self.assertTrue(self.markovChain.__repr__() != "")
            self.assertTrue(self.markovChain.getAllPossibleStates())
            self.assertTrue(self.markovChain.getMatrixAtStep(0), "matrix failed")

        loopDuration = 32
        self.cachedDataset.generateViewpoint("chords", sliceType=loopDuration)
        self.patternList = self.cachedDataset.getAllSliceOfDuration(loopDuration, viewpointName="chords")
        _testIt()
        self.patternList = self.cachedDataset.getAllSliceOfDuration(loopDuration)
        _testIt()
        # self.markovChain.plotMatrixAtStep(2)
        # self.markovChain.plotGlobalMatrix()

    def test_Markov_1_32_8(self):
        self.buildMarkov(1, 32, 16)
        # def test_Markov_2_32_4(self):
        # 	self.buildMarkov(2,32,4);
        # def test_Markov_3_32_4(self):
        # 	self.buildMarkov(3,32,4);
        # def test_Markov_4_32_4(self):
        # 	self.buildMarkov(4,32,4);

        # def test_Markov_1_16_4(self):
        # 	self.buildMarkov(1,16,4);
        # def test_Markov_2_16_4(self):
        # 	self.buildMarkov(2,16,4);
        # def test_Markov_3_16_4(self):
        # 	self.buildMarkov(3,16,4);
        # def test_Markov_4_16_4(self):
        # 	self.buildMarkov(4,16,4);

        # def test_Markov_1_16_2(self):
        # 	self.buildMarkov(1,16,2);
        # def test_Markov_2_16_2(self):
        # 	self.buildMarkov(2,16,2);
        # def test_Markov_3_16_2(self):
        # 	self.buildMarkov(3,16,2);
        # def test_Markov_4_32_2(self):
        # 	self.buildMarkov(4,16,2);

        # def test_Markov_1_32_8(self):
        # 	self.buildMarkov(1,32,8);
        # def test_Markov_2_32_8(self):
        # 	self.buildMarkov(2,32,8);
        # def test_Markov_3_32_8(self):
        # 	self.buildMarkov(3,32,8);
        # def test_Markov_4_32_8(self):
        # 	self.buildMarkov(4,32,8);

        # def test_random_markov(self):
        # 	numSteps = random.randint(4,128)
        # 	loopDuration = random.randint(1,16);
        # 	order = random.randint(0,numSteps-1);
        # 	self.buildMarkov(order = order,numSteps=numSteps,loopDuration=loopDuration)


if __name__ == "__main__":
    runTest(profile=False, getStat=False)
