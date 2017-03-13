from __future__ import absolute_import, division, print_function

import random

from .base_style import *
from ..gspattern import Pattern


class DatabaseStyle(BaseStyle):
    """
    A database based style. It generates patterns from already existing patterns

    Parameter
    ---------
    generatePatternOrdering: {'indexed', 'increasing', 'random'}
        Defines the generatePattern behaviour.

    """
    def __init__(self, generatePatternOrdering="indexed"):
        self.generatePatternOrdering = generatePatternOrdering
        self.patternList = []
        self.currentIdx = 0

    def generateStyle(self, PatternClasses):
        self.patternList = PatternClasses

    def generatePattern(self, seed=None):
        if self.generatePatternOrdering == 'increasing':
            p = self.patternList[self.currentIdx]
            self.currentIdx += 1
            print("reading", self.currentIdx)
            return p
        elif self.generatePatternOrdering == 'random':
            return self.patternList[int(random.random() * len(self.patternList))]
        elif self.generatePatternOrdering == 'indexed':
            return self.patternList[self.currentIdx]

    def getDistanceFromStyle(self, pattern):
        raise NotImplementedError("Should have implemented this")

    def getClosestPattern(self, pattern, seed=0):
        raise NotImplementedError("Should have implemented this")

    def getInterpolated(self, patternA, patternB, distanceFromA, seed=0):
        raise NotImplementedError("Should have implemented this")

    def getInternalState(self):
        res = {"patternList": []}
        for e in self.patternList:
            res["patternList"] += [e.toJSONDict()]
        return res

    def setInternalState(self, internalStateDict):
        self.patternList = []
        for e in internalStateDict["patternList"]:
            p = Pattern()
            p.fromJSONDict(e)
            self.patternList += [p]

    def isBuilt(self):
        self.patternList != []
