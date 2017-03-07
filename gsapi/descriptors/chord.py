from __future__ import absolute_import, division, print_function

from .baseDescriptor import *
from .density import Density
from ..patterns.utils import *
from ..utils.pitchSpelling import *


def intervalListToProfile(intervalList, length=12):
    profile = [-1] * length
    profile[0] = 1
    for e in intervalList:
        profile[e % length] = 0.8
    return profile


class ChordTag(tuple):
    """Helper to print chords tags nicely.
    Chord tags are tuples (root, type), ex : ('C','maj')
    """

    def __repr__(self):
        return "".join(self)


class Chord(BaseDescriptor):
    allProfiles = {key: intervalListToProfile(value) for key, value in chordTypes.items()}

    def __init__(self, forceMajMin=False, allowDuplicates=False):
        BaseDescriptor.__init__(self)
        self.densityDescriptor = Density()
        self.forceMajMin = forceMajMin
        self.allowDuplicates = allowDuplicates

    def configure(self, paramDict):
        """Configure current descriptor mapping dict to parameters."""
        raise NotImplementedError("Should have implemented this")

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
        bestScore = findBestScoreForProfiles(chromas,
                                             profileToConsider,
                                             penalityWeight=pattern.duration / 2.0,
                                             allowDuplicates=self.allowDuplicates)
        if self.allowDuplicates:
            return [ChordTag((defaultPitchNames[x[0]], x[1])) for x in bestScore]
        else:
            return ChordTag((defaultPitchNames[bestScore[0]], bestScore[1]))


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
