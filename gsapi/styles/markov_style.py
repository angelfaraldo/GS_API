
from __future__ import absolute_import, division, print_function

from .base_style import BaseStyle
from ..gspattern import PatternMarkov

import logging
markovLog = logging.getLogger('gsapi.styles.markov_style')


class MarkovStyle(BaseStyle):
    """
    Computes a style based on markov chains.

    Parameters
    ----------
    order: int
        order used for markov computation.
    numSteps: int
        number of steps to consider (binarization of pattern).

    """
    def __init__(self, order, numSteps, loopDuration):
        BaseStyle.__init__(self)
        self.type = "None"
        self.markovChain = PatternMarkov(order=order, numSteps=numSteps, loopDuration=loopDuration)

    def generateStyle(self, listOfPatterns):
        """
        Generates a style based on list of patterns.

        Parameters
        ----------
        listOfPatterns: list
            list of Patterns

        """
        self.markovChain.generateTransitionTableFromPatternList(listOfPatterns)

    def buildStyle(self):
        """
        Builds a transition table for a previously given list of patterns.

        """
        self.markovChain.buildTransitionTable()

    def generatePattern(self, seed=None):
        """Generates a new pattern.

        Parameters
        ----------
        seed: float
            seed for random initialisation of the pattern ('None' generates a new one).

        """
        return self.markovChain.generatePattern(seed=seed)

    def formatPattern(self, p):
        # p.quantize(self.loopDuration * 1.0 / self.numSteps, self.numSteps * 1.0/ self.loopDuration)
        p.timeStretch(self.numSteps * 1.0 / self.loopDuration)
        p.alignOnGrid(1)
        p.removeOverlapped()
        p.fillWithSilences(maxSilenceTime=1)

    def getLastEvents(self, pattern, step, num, stepSize):
        events = []
        for i in reversed(range(1, num+1)):
            idx = step - i * stepSize
            if idx < 0:
                idx += pattern.duration
            events += [pattern.getStartingEventsAtTime(idx)]
        return events

    def getDistanceFromStyle(self, Pattern):
        raise NotImplementedError("Not Implemented.")

    def getClosestPattern(self, Pattern, seed=0):
        raise NotImplementedError("Not Implemented.")

    def getInterpolated(self, PatternA, PatternB, distanceFromA, seed=0):
        raise NotImplementedError("Not Implemented.")

    def getInternalState(self):
        res = {"markovChain": self.markovChain.getInternalState()}
        return res

    def setInternalState(self, state):
        self.markovChain.setInternalState(state["markovChain"])

    def isBuilt(self):
        return self.markovChain.isBuilt()
