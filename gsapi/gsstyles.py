from __future__ import absolute_import, division, print_function

import copy
import logging
import random

from .gspattern import Pattern

markovLog = logging.getLogger('gsapi.styles.markov_style')
# todo change this to fit the new reorganisation!


class BaseStyle(object):
    """
    Base class to define a style.

    Such class needs to provide the following methods:
        - generateStyle(self, PatternClasses)
        - generatePattern(self, seed=None)
        - getDistanceFromStyle(self, Pattern)
        - getClosestPattern(self, Pattern, seed=None)
        - getInterpolated(self, PatternA, PatternB, distanceFromA, seed=None)
        - getInternalState(self)
        - loadInternalState(self, internalStateDict)
        - isBuilt(self)

    """
    def __init__(self):
        self.type = "style"

    def generateStyle(self, PatternClasses):
        """
        Computes inner state of style based on a list of patterns.

        """
        raise NotImplementedError("Not Implemented.")

    def generatePattern(self, seed=None):
        """
        Generates a new random pattern using a seed if not "None".
        Ideally same seed should lead to same pattern.

        """
        raise NotImplementedError("Not Implemented.")

    def getDistanceFromStyle(self, Pattern):
        """
        Returns a normalized value representing the 'styleness' of a pattern.
        1 represents the farthest from the style, 0 the closest.

        """
        raise NotImplementedError("Not Implemented.")

    def getClosestPattern(self, Pattern, seed=None):
        """
        Returns the closest pattern in this style.

        """
        raise NotImplementedError("Not Implemented.")

    def getInterpolated(self, PatternA, PatternB, distanceFromA, seed=0):
        """
        Interpolates between two patterns given this style constraints.

        """
        raise NotImplementedError("Not Implemented.")

    def getInternalState(self):
        """
        Returns a dict representing the current internal state.

        """
        raise NotImplementedError("Not Implemented.")

    def setInternalState(self, internalStateDict):
        """
        Loads internal state from a given dict.

        """
        raise NotImplementedError("Not Implemented.")

    def isBuilt(self):
        """
        Returns True if the style has been correctly build.

        """
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
        import sys
        if sys.version_info >= (3, 0):
            import pickle
        else:
            import cPickle as pickle
        pickle.dump(self, filePath)

    def loadFromPickle(self, filePath):
        import sys
        if sys.version_info >= (3, 0):
            import pickle
        else:
            import cPickle as pickle
        self = pickle.load(filePath)


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

    def __init__(self, order=2, numSteps=16, loopDuration=4):
        # BaseStyle.__init__(self)
        # self.type = "Style"
        self.markovChain = PatternMarkov(order=order, numSteps=numSteps,
                                         loopDuration=loopDuration)

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
            seed for random initialisation of the pattern.
            ('None' generates a new one).

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
        for i in reversed(range(1, num + 1)):
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


class PatternMarkov(object):
    """
    Computes a Markov chain from pattern.

    Parameters
    ----------
    order: int
        order used for markov computation
    numSteps: int
        number of steps to consider (binarization of pattern)

    """

    def __init__(self, order=1, numSteps=32, loopDuration=4):
        self.order = order
        self.numSteps = numSteps
        self.loopDuration = loopDuration
        self.transitionTable = {}

    def generateTransitionTableFromPatternList(self, patternClasses):
        """Generate style based on list of Pattern
        Args:
            patternClasses:  list of GSPatterns
        """
        if not isinstance(patternClasses, list):
            markovLog.error("PatternMarkov needs a list of patterns")
            return False
        else:
            self.originPatterns = patternClasses
            self.buildTransitionTable()

    def getMarkovConfig(self):
        return "order(%i), loopLength(%f), numSteps(%i)" % (
            self.order, self.loopDuration, self.numSteps)

    def buildTransitionTable(self):
        """
        Builds a transition table with the previously given list of Patterns.

        """
        self.transitionTable = [{} for f in range(int(self.numSteps))]

        self.binarizedPatterns = copy.deepcopy(self.originPatterns)
        for p in self.binarizedPatterns:
            self.formatPattern(p)
            self.checkSilences(p)
            if self.numSteps != int(p.duration):
                markovLog.warning(
                        "PatternMarkov: quantization to numSteps failed, numSteps=" + str(
                                self.numSteps) + " duration=" + str(
                                p.duration) + " cfg : " + self.getMarkovConfig())
            for step in range(self.numSteps):
                l = [p.getStartingEventsAtTime(step)]
                self.checkSilenceInList(l)
                curEvent = self._buildTupleForEvents(l)[0]
                combinationName = self._buildTupleForEvents(
                        self.getLastEvents(p, step, self.order, 1))

                curDic = self.transitionTable[int(step)]

                if combinationName not in curDic:
                    curDic[combinationName] = {}

                if curEvent not in curDic[combinationName]:
                    curDic[combinationName][curEvent] = 1
                else:
                    curDic[combinationName][curEvent] += 1

        def _normalize():
            for t in self.transitionTable:
                for d in t:
                    sum = 0
                    for pe in t[d]:
                        sum += t[d][pe]
                    for pe in t[d]:
                        t[d][pe] /= 1.0 * sum

        _normalize()

    def getStringTransitionTable(self, reduceTuples=True, jsonStyle=True):
        import copy
        stringTable = copy.deepcopy(self.transitionTable)

        def _tupleToString(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(k, tuple):
                        d[str(_tupleToString(k))] = d.pop(k)
                    _tupleToString(v)
            elif isinstance(d, list):
                for v in d:
                    _tupleToString(v)
            elif isinstance(d, tuple):
                newTuple = ()
                for v in d:
                    newTuple += (_tupleToString(v),)
                if reduceTuples and len(newTuple) == 1:
                    newTuple = newTuple[0]
                d = newTuple
            return d

        for t in stringTable:
            t = _tupleToString(stringTable)

        if jsonStyle:
            import json

            for i in range(len(stringTable)):
                stringTable[i] = json.dumps(stringTable[i], indent=1)

        return stringTable

    def __repr__(self):
        res = "Markov Transition Table\n"
        st = self.getStringTransitionTable(reduceTuples=True, jsonStyle=True)
        i = 0
        for t in st:
            res += "step %d\n%s\n" % (i, t)
            i += 1
        return res

    def generatePattern(self, seed=None):
        """Generate a new pattern from current transitionTable.

        Args:
            seed: seed used for random initialisation of pattern (value of None generates a new one)
        """
        random.seed(seed)
        potentialStartEvent = []

        def _getAvailableAtStep(step):
            res = []
            if step < 0:
                step += len(self.transitionTable)
            for n in self.transitionTable[step]:
                for t in self.transitionTable[step][n]:
                    res += [t]
            return res

        def _isValidState(step, previousTags):
            d = self.transitionTable[step]
            # print(d)
            # print(previousTags)
            return previousTags in d

        def _generateEventAtStep(step, previousTags):

            if previousTags not in self.transitionTable[step]:
                markovLog.error(
                        "wrong transition table, zero state for " + str(
                                previousTags))
                markovLog.error(str(self.transitionTable[step]))
                return None
            d = self.transitionTable[step][previousTags]
            chosenIdx = 0
            if len(d) > 1:
                tSum = 0
                bins = []
                for x in d.values():
                    tSum += x
                    bins += [tSum]
                r = random.random()
                for i in range(1, len(bins)):
                    if bins[i - 1] <= r and bins[i] > r:
                        chosenIdx = i - 1
                        break

            return list(d.keys())[chosenIdx]

        cIdx = self.order
        startHypothesis = tuple()
        maxNumtries = 30
        while not _isValidState(cIdx, startHypothesis):
            startHypothesis = tuple()
            for n in range(self.order):
                startHypothesis += (random.choice(_getAvailableAtStep(n)),)
            maxNumtries -= 1
            if maxNumtries == 0:
                raise Exception("Can't find start hypothesis in markov")

        events = list(startHypothesis)
        i = self.order
        maxNumtries = 10
        maxTries = maxNumtries
        while i < self.numSteps and maxTries > 0:
            newPast = tuple(events[i - self.order:i])
            newEv = _generateEventAtStep(i, newPast)
            if newEv:
                events += [newEv]
                maxTries = maxNumtries
                i += 1
            else:
                maxTries -= 1
                if maxTries == 0:
                    markovLog.error(
                            "not found combination %s at step %i \n transitions\n %s" % (
                                ','.join(newPast), i, self.transitionTable[i]))
                    raise Exception(" can't find combination in markov")
                else:
                    markovLog.warning(
                            "not found combination %s " % (','.join(newPast)))

        pattern = gspattern.Pattern()
        idx = 0

        stepSize = 1.0 * self.loopDuration / self.numSteps

        for el in events:
            for tagElem in el:
                if tagElem != 'silence':
                    pattern.events += [
                        gspattern.Event(idx * stepSize, stepSize, 100, 127,
                                        tag=tagElem)]

            idx += 1
        pattern.duration = self.loopDuration

        return pattern

    def checkSilences(self, p):
        for i in range(int(p.duration)):
            c = p.getStartingEventsAtTime(i)
            if len(c) > 1 and ("silence" in c):
                markovLog.error("wrong silence")

    def checkSilenceInList(self, c):
        if len(c) > 1 and ('silence' in c):
            markovLog.error("wrong silence")

    def _buildTupleForEvents(self, events):
        """Build a tuple from list of lists of events:
        If list is [[a1, a2], [b1, b2, b3]] (where an and bn are tags of listed events)
        this function returns "a1/a2, b1/b2/b3"
        """
        res = tuple()
        for evAtStep in events:
            curL = list()
            for e in evAtStep:
                curL += [e.tag]

            # set allow for having consistent ordering, and remove step-wise overlapping events
            res += (tuple(set(curL)),)
        return res

    def formatPattern(self, p):
        """Format pattern to have a grid aligned on markov steps size."""
        # p.quantize(self.loopDuration*1.0/self.numSteps);
        p.timeStretch(self.numSteps * 1.0 / self.loopDuration)

        p.alignOnGrid(1)
        p.removeOverlapped()
        p.fillWithSilences(maxSilenceTime=1)

    def getLastEvents(self, pattern, step, num, stepSize):
        events = []
        for i in reversed(range(1, num + 1)):
            idx = step - i * stepSize
            if idx < 0:
                idx += pattern.duration
            events += [pattern.getStartingEventsAtTime(idx)]
        return events

    def getInternalState(self):
        """utility function to save current state
        """
        res = {"transitionTable": self.transitionTable, "order": self.order,
               "numSteps":        self.numSteps,
               "loopDuration":    self.loopDuration}
        return res

    def setInternalState(self, state):
        """
        Utility function to load the current state.
        """
        self.transitionTable = state["transitionTable"]
        self.order = state["order"]
        self.numSteps = state["numSteps"]
        self.loopDuration = state["loopDuration"]

    def isBuilt(self):
        return self.transitionTable != {}

    def getAllPossibleStates(self):
        possibleStates = []
        for d in self.transitionTable:
            possibleStates += list(d.keys())
            for v in d.values():
                for state in v.keys():
                    possibleStates += [state]
        possibleStates = list(set(possibleStates))
        return possibleStates

    def getAllPossibleStatesAtStep(self, step):
        return list(set(self.getPossibleInStatesAtStep(
                step) + self.getPossibleOutStatesAtStep(step)))

    def getPossibleOutStatesAtStep(self, step):
        if step < 0: step += len(self.transitionTable)
        step %= len(self.transitionTable)
        d = self.transitionTable[step]
        possibleStates = []
        for v in d.values():
            for state in v.keys():
                possibleStates += [state]
        possibleStates = list(set(possibleStates))
        return possibleStates

    def getPossibleInStatesAtStep(self, step):
        if step < 0: step += len(self.transitionTable)
        step %= len(self.transitionTable)
        d = self.transitionTable[step]
        return list(d.keys())

    def getMatrixAtStep(self, step, possibleStatesIn=None,
                        possibleStatesOut=None, matrix=None):
        if step < 0: step += len(self.transitionTable)
        possibleStatesIn = possibleStatesIn or self.getPossibleInStatesAtStep(
                step)
        possibleStatesOut = possibleStatesOut or self.getPossibleOutStatesAtStep(
                step)
        sizeIn = len(possibleStatesIn)
        sizeOut = len(possibleStatesOut)
        matrix = matrix or [[0] * sizeOut for i in range(sizeIn)]
        d = self.transitionTable[step]
        for k, v in d.items():
            colIdx = possibleStatesIn.index(k)
            for evt, p in v.items():
                rowIdx = possibleStatesOut.index(evt)
                matrix[colIdx][rowIdx] += p

        return matrix, possibleStatesIn, possibleStatesOut

    def __plotMatrix(self, m, labelsIn, labelsOut):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()  # figsize=(18, 2))
        # shows zero values as black
        cmap = plt.cm.OrRd
        cmap.set_under(color='black')
        cax = ax.matshow(m, interpolation='nearest', vmin=0.000001, cmap=cmap)
        ax.set_xticks(range(len(labelsOut)))
        ax.set_xticklabels(labelsOut, rotation='vertical')
        ax.set_yticks(range(len(labelsIn)))
        ax.set_yticklabels(labelsIn)
        fig.colorbar(cax)
        plt.show()

    def plotMatrixAtStep(self, step):
        if step < 0: step += len(self.transitionTable)
        mat, labelsIn, labelsOut = self.getMatrixAtStep(
                step)  # ,possibleStates = allTags)
        self.__plotMatrix(mat, labelsIn, labelsOut)

    def plotGlobalMatrix(self):
        numSteps = len(self.transitionTable)
        possibleStatesIn = list(set(
                [item for step in range(numSteps) for item in
                 self.getPossibleInStatesAtStep(step)]))
        possibleStatesOut = list(set(
                [item for step in range(numSteps) for item in
                 self.getPossibleOutStatesAtStep(step)]))
        sizeIn = len(possibleStatesIn)
        sizeOut = len(possibleStatesOut)
        matrix = [[0] * sizeOut for i in range(sizeIn)]
        for step in range(numSteps):
            self.getMatrixAtStep(step, possibleStatesIn=possibleStatesIn,
                                 possibleStatesOut=possibleStatesOut,
                                 matrix=matrix)
        self.__plotMatrix(matrix, possibleStatesIn, possibleStatesOut)




