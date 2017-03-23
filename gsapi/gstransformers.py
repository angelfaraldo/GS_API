from __future__ import absolute_import, division, print_function

import random
from .gsdescriptors import Density
from .gspattern import Event


class BaseTransformer(object):
    """
    Base class for defining a transform algorithm.

    Methods
    -------
    configure: dict
        configure current transformer based on implementation specific parameters passed in the dict argument
    transformPattern: pattern
        return a transformed version of Pattern

    """

    def __init__(self):
        self.type = "Transformer"

    def configure(self, paramDict):
        """
        Configure the current transformer based on implementation
        specific parameters passed in paramDict argument.

        Parameters
        ----------
        paramDict: dict
            a dictionary with configuration values.

        """
        raise NotImplementedError("Not Implemented.")

    def transformPattern(self, pattern):
        """
        Returns a transformed pattern.

        Parameters
        ----------
        pattern: pattern
            the pattern to be transformed.

        Returns
        -------
            a transformed pattern.
        """
        raise NotImplementedError("Not Implemented.")


class AgnosticDensity(BaseTransformer):
    """
    Agnostic Density transformer algorithm.

    Argsuments
    ----------
    numSteps: int
        number of steps to consider.
    mode: ['random','syncopation']
        type of algorithm used.
    globalDensity: float (0..2)
        the desired global density (0 = empty pattern, 1 = origin pattern, 2 = pattern with all events)
    individualDensities: dict
        dict[tag]=density: a specific density on a per-Tag basis.
        Densities should be in the same range as globalDensity
    originPattern: pattern
        the origin pattern (e.g: the one given if all densities are equals to 1).

    """

    def __init__(self, mode='random', numSteps=32):
        self.globalDensity = 1
        self.normalizedDensities = {}
        self.targetDensities = {}
        self.mode = mode
        self.originPattern = None
        self.currentPattern = None
        self.originDuration = 0
        self.numSteps = numSteps
        self.originDensities = {}
        self.densityDescriptor = Density()
        self.currentDistribution = {}
        self.currentState = {}
        self.originDistribution = {}

    def configure(self, paramDict):
        if 'inputPattern' in paramDict:
            self.buildDensityMap(paramDict['inputPattern'])  # TODO: Faltaba el self.

    def transformPattern(self, pattern, paramDict):
        if pattern is not None and pattern != self.originPattern:
            self.buildDensityMap(pattern)
        if self.originPattern is None:
            return
        if 'normalizedDensities' in paramDict:
            self.updateNormalizedDensities(paramDict['normalizedDensities'])
        res = self.currentPattern.copy()
        res.timeStretch(self.originDuration * 1.0 / self.numSteps)
        return res

    def updateNormalizedDensities(self, normalizedDict):
        for key, value in normalizedDict.items():
            if key in self.normalizedDensities:
                originDensity = self.normalizedDensities[key]
                # if we cross density one, reset to one then do the subsequent calculations
                if (value < 1 < originDensity) or (value > 1 > originDensity):
                    # print "reset densities"
                    self.resetDensities()

                diffNormalized = value - self.normalizedDensities[key]
                if diffNormalized == 0:
                    continue

                # here we are sure to not need to crossdensity one (and have to do both increment styles)
                if originDensity >= 1 and value >= 1:
                    step = 1.0 / (self.numSteps - self.originDensities[key])
                    number = originDensity
                    value = max(1, min(value, 2)) - step
                    if diffNormalized > step:

                        while number < value:
                            self.addEventForTag(key, number)
                            number += step
                    if diffNormalized < -step:
                        while number > value:
                            self.removeEventForTag(key, number)
                            number -= step
                    self.normalizedDensities[key] = 1.0 + int((value - 1.0) / step) * 1.0 * step

                if originDensity <= 1 and value < 1:
                    step = 1.0 / (self.originDensities[key])
                    number = originDensity
                    value = max(0, min(value, 1)) + step
                    if diffNormalized > step:
                        while number < value:
                            self.addEventForTag(key, number)
                            number += step
                    if diffNormalized < -step:
                        while number > value:
                            self.removeEventForTag(key, number)
                            number -= step
                    self.normalizedDensities[key] = int(value / step) * 1.0 * step
        self.currentPattern.reorderEvents()

    def addEventForTag(self, tag, targetDensity):

        availableIdx = self.currentState[tag]['silences']
        # we need to go toward origin pattern if adding while having lower density
        if targetDensity < 1:
            availableIdx = self.currentState[tag]['removedNotes']

        idx = 0
        if self.mode == 'hysteresis':
            idx = random.randint(0, len(availableIdx) - 1)

        idxToAdd = availableIdx[idx]

        orIdx = self.currentState[tag]['silences'].index(idxToAdd)
        del self.currentState[tag]['silences'][orIdx]
        if targetDensity < 1:
            del self.currentState[tag]['removedNotes'][idx]

        self.currentState[tag]['addedNotes'] += [idxToAdd]
        tPattern = self.currentPattern.getPatternWithTags(tag, makeCopy=False)
        newEv = tPattern.events[0].copy()
        newEv.startTime = idxToAdd
        newEv.duration = 1
        self.currentPattern.events += [newEv]

    def removeEventForTag(self, tag, targetDensity):

        availableIdx = self.currentState[tag]['notes']

        # we need to go toward origin pattern if removing while having higher density
        if targetDensity > 1:
            availableIdx = self.currentState[tag]['addedNotes']

        idx = 0
        if self.mode == 'hysteresis':
            idx = random.randint(0, len(availableIdx) - 1)

        idxToRemove = availableIdx[idx]

        orIdx = self.currentState[tag]['notes'].index(idxToRemove)
        del self.currentState[tag]['notes'][orIdx]
        if targetDensity > 1:
            del self.currentState[tag]['addedNotes'][idx]

        self.currentState[tag]['removedNotes'] += [idxToRemove]
        tPattern = self.currentPattern.getPatternWithTags(tag, makeCopy=False)

        eventToRemove = tPattern.getStartingEventsAtTime(idxToRemove)[0]
        self.currentPattern.removeEvent(eventToRemove)

    def createCurrentState(self):
        self.currentState = {}
        for tag in self.originPattern.getAllTags():
            dist = self.__initStateFromVoice(self.originPattern.getPatternWithTags(tag))
            self.currentState[tag] = dist

    def __shuffleList(self, l):
        for iteration in range(len(l)):
            idx1 = iteration
            idx2 = random.randint(0, len(l) - 1)
            t = l[idx1]
            l[idx1] = l[idx2]
            l[idx2] = t

    def __initStateFromVoice(self, voice):
        state = {'notes': [], 'silences': [], 'addedNotes': [], 'removedNotes': []}
        curEvent = voice.events[0]
        curEvtIdx = 0
        for t in range(self.numSteps):
            if curEvent.containsTime(t):
                curEvtIdx += 1
                curEvtIdx = min(len(voice.events) - 1, curEvtIdx)
                curEvent = voice.events[curEvtIdx]
                state['notes'] += [t]
            else:
                state['silences'] += [t]
        self.__shuffleList(state['notes'])
        self.__shuffleList(state['silences'])
        return state

    def resetDensities(self):
        self.originDensities = {}
        self.targetDensities = {}
        self.normalizedDensities = {}
        for t in self.originPattern.getAllTags():
            self.densityDescriptor.includedTags = t
            density = self.densityDescriptor.getDescriptorForPattern(self.originPattern)
            self.originDensities[t] = density * self.numSteps * 1.0 / self.originPattern.duration
            self.targetDensities[t] = density * self.numSteps * 1.0 / self.originPattern.duration
            self.normalizedDensities[t] = 1

    def buildDensityMap(self, pattern):
        self.originPattern = pattern.copy()
        self.originDuration = pattern.duration
        self.originPattern.timeStretch(self.numSteps * 1.0 / self.originPattern.duration)
        self.originPattern.alignOnGrid(1)
        self.currentPattern = self.originPattern.copy()
        self.resetDensities()
        self.createCurrentState()


class EventChord(Event):
    """Represents an event of a pattern.
    An event has a startTime, duration, pitch, velocity and associated tags.

    Class variables:
        startTime: startTime of event
        duration: duration of event
        pitch: pitches of event
        velocity: velocity of event
        tags: list of tags representing the event
    """

    # LEGACY CLASS: could be replaced by Pattern.generateViewpoint("chords")

    def __init__(self, startTime=0, duration=1.0, components=None, tag=None, label="chord"):
        Event.__init__(self, startTime=startTime, duration=duration, tag=tag)
        self.components = components or []
        self.label = label

    def __repr__(self):
        return "%s %s %s %05.2f %05.2f" % (self.label,
                                           self.tag,
                                           str(self.components),
                                           self.startTime,
                                           self.duration)


class Chordify(BaseTransformer):
    """Makes vertical slices of a pattern"""

    def __init__(self, pattern):
        self.inputPattern = pattern
        self.outputPattern = self.transformPattern()
        self.duration = self.outputPattern.duration
        self.events = self.outputPattern.events
        self.numChords = len(self.outputPattern.events)

    def configure(self, paramDict):
        """Configure current transformer based on implementation
        specific parameters passed in paramDict argument.

        Args:
            paramDict: a dictionary with configuration values
        """
        raise NotImplementedError("Not Implemented.")

    def transformPattern(self):
        """Return a transformed Pattern"""
        self.outputPattern = self.inputPattern.copyWithoutEvents()
        p = -1
        for e in self.inputPattern:
            if e.startTime != p:
                new_chord = EventChord(startTime=e.startTime, duration=e.duration, components=[], tag=())
                for ee in self.inputPattern.activeEventsAtTime(e.startTime):
                    new_chord.components.append([ee.pitch, ee.velocity])
                    for tag in ee.tag:
                        new_chord.tag.append(tag)
                self.outputPattern.addEvent(new_chord)
            p = e.startTime
        return self.outputPattern



