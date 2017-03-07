from __future__ import absolute_import, division, print_function

from ..patterns.pattern import Pattern
# import random
# import copy


class BaseStyle(object):
    """Base class for defining a style.
    Such class needs to provide the following functions:
        - generateStyle(self, PatternClasses)
        - generatePattern(self, seed=None)
        - getDistanceFromStyle(self, Pattern)
        - getClosestPattern(self, Pattern, seed=None)
        - getInterpolated(self, PatternA, PatternB, distanceFromA, seed=None)
        - getInternalState(self)
        - loadInternalState(self, internalStateDict)
        - isBuilt(self)"""
    def __init__(self):
        self.type = "None"

    def generateStyle(self, PatternClasses):
        """Computes inner state of style based on list of patterns."""
        raise NotImplementedError("Not Implemented.")

    def generatePattern(self, seed=None):
        """Generates a new random pattern using seed if not "None"
        (Ideally same seeds should lead to same patterns.)"""
        raise NotImplementedError("Not Implemented.")

    def getDistanceFromStyle(self, Pattern):
        """Returns a normalized value representing the "styliness"
         of a pattern 1 being farthest from style."""
        raise NotImplementedError("Not Implemented.")

    def getClosestPattern(self, Pattern, seed=None):
        """Returns the closest pattern in this style."""
        raise NotImplementedError("Not Implemented.")

    def getInterpolated(self, PatternA, PatternB, distanceFromA, seed=0):
        """Interpolates between two patterns given this style constraints."""
        raise NotImplementedError("Not Implemented.")

    def getInternalState(self):
        """Returns a dict representing the current internal state."""
        raise NotImplementedError("Not Implemented.")

    def setInternalState(self, internalStateDict):
        """Loads internal state from a given dict."""
        raise NotImplementedError("Not Implemented.")

    def isBuilt(self):
        """Returns true if style hasbeen correctly build."""
        raise NotImplementedError("Not Implemented.")

    def saveToJSON(self, filePath):
        import json
        state = self.getInternalState()
        with open(filePath, 'w') as f:
            json.dump(state, f)

    def loadFromJSON(self, filePath):
        import json
        with open(filePath, 'r') as f:
            state = json.load(f)
        if state:
            self.setInternalState(state)

    def saveToPickle(self, filePath):
        import cPickle
        cPickle.dump(self, filePath)

    def loadFromPickle(self, filePath):
        import cPickle
        self = cPickle.load(filePath)
