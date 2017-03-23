#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from math import ceil

from . import gsdefs

### FUNCTION Definitions!

def intervalListToProfile(intervalList, length=12):
    profile = [-1] * length
    profile[0] = 1
    for e in intervalList:
        profile[e % length] = 0.8
    return profile


def findBestScoreForProfiles(chromas, pitchProfileDict, penalityWeight, allowDuplicates=False):
    maxScore = 0
    if allowDuplicates:
        bestProfile = []
        bestRoot = []
    else:
        bestProfile = ""
        bestRoot = 0
    for key, value in pitchProfileDict.items():
        conv = convolveWithPitchProfile(chromas, value, penalityWeight)
        score = findMaxAndIdx(conv)
        nonZero = getNumNonZero(value)  # todo: what is this for?
        if score[0] >= maxScore:
            if allowDuplicates:
                if score[0] > maxScore:
                    bestProfile = [key]
                    bestRoot = [score[1]]
                else:
                    bestProfile += [key]
                    bestRoot += [score[1]]
            else:
                bestProfile = key
                bestRoot = score[1]
            maxScore = score[0]
    if allowDuplicates:
        return [(bestRoot[i], bestProfile[i]) for i in range(len(bestRoot))]
    else:
        return bestRoot, bestProfile


def getNumNonZero(li):
    count = 0
    for e in li:
        if e != 0:
            count += 1
    return count


def convolveWithPitchProfile(chromas, pitchProfile, penalityWeight):
    if len(pitchProfile) != len(chromas):
        print('chroma and pitchProfile of different length')
        return None

    convLen = len(chromas)
    convList = [0] * convLen
    for i in range(convLen):
        conv = 0
        for chroma in range(convLen):
            idx = (chroma - i + convLen) % convLen
            conv += chromas[chroma] * pitchProfile[idx]

            # penalize if notes from pitch profile are missing
            if pitchProfile[idx] > 0 >= chromas[chroma]:
                conv -= penalityWeight
        convList[i] = conv
    return convList


def findMaxAndIdx(convolution):
    M = 0
    Mi = -1
    i = 0
    for chroma in convolution:
        if chroma > M:
            M = chroma
            Mi = i
        i += 1
    return [M, Mi]


class BaseDescriptor(object):
    def __init__(self):
        self.type = "descriptor"

    def configure(self, paramDict):
        """
        Configure the current descriptor mapping dict to parameters.

        """
        raise NotImplementedError("Not Implemented.")

    def getDescriptorForPattern(self, pattern):
        """
        Compute a unique value for a given pattern.
        It can be a sliced part of a bigger one.

        """
        raise NotImplementedError("Not Implemented.")


class Density(BaseDescriptor):
    def __init__(self, ignoredTags=None, includedTags=None):
        BaseDescriptor.__init__(self)
        self.ignoredTags = ignoredTags or ["silence"]
        self.includedTags = includedTags

    def configure(self, paramDict):
        """
        Configure current descriptor mapping dict to parameters.

        """
        raise NotImplementedError("Not Implemented.")

    def getDescriptorForPattern(self, pattern):
        density = 0
        _checkedPattern = pattern.getPatternWithoutTags(tagToLookFor=self.ignoredTags)
        if self.includedTags:
            _checkedPattern = _checkedPattern.getPatternWithTags(tagToLookFor=self.includedTags, makeCopy=False)
        for e in _checkedPattern.events:
            density += e.duration
        return density


class NumberOfTags(BaseDescriptor):
    """
    Calculates the number of tags in a given Pattern.

    """

    def __init__(self, ignoredTags=None, includedTags=None):
        BaseDescriptor.__init__(self)
        self.ignoredTags = ignoredTags or ["silence"]
        self.includedTags = includedTags

    def configure(self, paramDict):
        """
        Configure current descriptor mapping dict to parameters.

        """
        raise NotImplementedError("Not Implemented.")

    def getDescriptorForPattern(self, pattern):
        _checkedPattern = pattern.getPatternWithoutTags(tagToLookFor=self.ignoredTags)
        if self.includedTags:
            _checkedPattern = _checkedPattern.getPatternWithTags(tagToLookFor=self.includedTags, makeCopy=False)
        return len(_checkedPattern.getAllTags())


class Syncopation(BaseDescriptor):
    """
    Computes the syncopation value of a pattern.

    """

    def __init__(self):
        BaseDescriptor.__init__(self)
        self.weights = []
        self.noteGrid = []
        self.duration = 1

    def configure(self, paramDict):
        """
        Configure current descriptor mapping dict to parameters.

        """
        raise NotImplementedError("Not Implemented.")

    def __buildSyncopationWeight(self):
        depth = 1
        self.weights = [0] * int(self.duration)
        thresh = 0
        stepWidth = int(self.duration * 1.0 / depth)
        while stepWidth > thresh:
            for s in range(depth):
                self.weights[s * stepWidth] += 1
            depth *= 2
            stepWidth = int(self.duration * 1.0 / depth)

    def __buildBinarizedGrid(self, pattern):
        self.noteGrid = [0] * self.duration
        for i in range(self.duration):
            self.noteGrid[i] = len(pattern.activeEventsAtTime(i))

    def getDescriptorForPattern(self, pattern):
        self.duration = int(ceil(pattern.duration))
        if not self.weights or (self.duration != len(self.weights)):
            self.__buildSyncopationWeight()
        syncopation = 0

        self.__buildBinarizedGrid(pattern)
        for t in range(self.duration):
            nextT = (t + 1) % self.duration
            if self.noteGrid[t] and not self.noteGrid[nextT]:
                syncopation += abs(self.weights[nextT] - self.weights[t])
        return syncopation


class ChordTag(tuple):
    """
    Helper to print chords tags nicely.
    Chord tags are tuples (root, type), ex : ('C','maj').

    """

    def __repr__(self):
        return "".join(self)


class Chord(BaseDescriptor):
    allProfiles = {key: intervalListToProfile(value) for key, value in gsdefs.chordTypes.items()}

    def __init__(self, forceMajMin=False, allowDuplicates=False):
        BaseDescriptor.__init__(self)
        self.densityDescriptor = Density()
        self.forceMajMin = forceMajMin
        self.allowDuplicates = allowDuplicates

    def configure(self, paramDict):
        """
        Configure current descriptor mapping dict to parameters.

        """
        raise NotImplementedError("Not Implemented.")

    def getDescriptorForPattern(self, pattern):
        allPitches = pattern.getAllPitches()
        pitchDensities = {}

        for pitch in allPitches:
            voice = pattern.getPatternWithPitch(pitch)
            pitchDensities[pitch] = self.densityDescriptor.getDescriptorForPattern(voice)

        chromas = [0] * 12
        for pitch, value in pitchDensities.items():
            chroma = pitch % 12
            chromas[chroma] += value

        elemNum = 0
        for chroma in chromas:
            if chroma > 0:
                elemNum += 1

        if elemNum == 0:
            return "silence"
        ordered = [{'chroma': i, 'density': chromas[i]} for i in range(len(chromas))]
        ordered.sort(key=lambda equis: (equis['density']))
        profileToConsider = Chord.allProfiles
        if self.forceMajMin:
            profileToConsider = {'min': profileToConsider['min'], 'maj': profileToConsider['maj']}
        bestScore = findBestScoreForProfiles(chromas, profileToConsider, penalityWeight=pattern.duration / 2.0,
                                             allowDuplicates=self.allowDuplicates)
        if self.allowDuplicates:
            return [ChordTag((gsdefs.defaultPitchNames[x[0]], x[1])) for x in bestScore]
        else:
            return ChordTag((gsdefs.defaultPitchNames[bestScore[0]], bestScore[1]))
