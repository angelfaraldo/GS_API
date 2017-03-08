#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

import logging
import copy
import math
import collections
import os
import random

from . import gsutil
from . import gsdefs
from .gsio import *


# logger for pattern related operations
patternLog = logging.getLogger("gsapi.pattern")


class Event(object):
    """
    Represents an event of a pattern with startTime, duration, pitch,
    velocity and one or integration tags.

    Parameters
    ----------
    startTime: float
        startTime of event.
    duration: float
        duration of event.
    pitch: int
        pitch of event in midi note numbers.
    velocity: int
        velocity of event in midi format (0-127).
    tag: string, tuple, object
        any hashable object representing the event, except lists.
    originPattern: Pattern
        keeps track of origin pattern for events generated from pattern,
        e.g., a chord event can still access to its individual components
        via originPattern (see Pattern.generateViewpoints)

    """

    def __init__(self, startTime=0, duration=1, pitch=60, velocity=80,
                 tag=None, originPattern=None):

        self.startTime = startTime
        self.duration = duration
        self.pitch = pitch
        self.velocity = velocity
        self.originPattern = originPattern

        if not tag:
            self.tag = ()
        elif isinstance(tag, list):
            patternLog.error("tag cannot be a list, converting to tuple")
            self.tag = tuple(tag)
        elif not isinstance(tag, collections.Hashable):
            patternLog.error("tag has to be hashable, trying conversion to tuple")
            self.tag = (tag,)
        else:
            self.tag = tag

    def __repr__(self):
        return "%s %i %i %05.4f %05.4f" % (self.tag, self.pitch, self.velocity,
                                           self.startTime, self.duration)

    def __eq__(self, other):
        if isinstance(other, Event):
            return (self.startTime == other.startTime) and \
                   (self.pitch == other.pitch) and \
                   (self.velocity == other.velocity) and \
                   (self.duration == other.duration) \
                   and (self.tag == other.tag)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def hasOneCommonTagWith(self, event):
        """
        Compare tags between events

        Parameters
        ----------
        event: Event
            event to compare with

        Returns
        -------
        Boolean
            True if at least one tag is equal

        """
        # if type(self.tag)!=type(event.tag):
        #     return False
        return self.hasOneOfTags(event.tag)

    def hasOneOfTags(self, tags):
        """
        Compare this event's tags with a list of possible tag.

        Args:
            tags: list of tags to compare with
        Returns:
            True if at least one tag is equal
        """
        for t in tags:
            if (t == self.tag) or (t in self.tag):
                return True
        return False

    def tagIs(self, tag):
        """Compare this event's tag with a a given tag.

        Args:
            tag: tag to compare with
        Returns:
            True if all event tag is equal to given tag
        """
        return self.tag == tag

    def allTagsAreEqualWith(self, event):
        """Compare this event's tag with an other event.

        Args:
            event: event to compare with
        Returns:
            True if tags are equal
        """
        self.tagIs(event.tag)

    def getEndTime(self):
        """Return the time when this events ends

        Returns:
            The time when this event ends
        """
        return self.startTime + self.duration

    def copy(self):
        """ Copy an event.

        Returns:
            A deep copy of this event to be manipulated without changing
            original.
        """
        return copy.deepcopy(self)

    def cutInSteps(self, stepSize):
        """ Cut an event in steps of stepsize length

        Args:
            stepSize: the desired size of each produced events
        Returns:
            a list of events of length `stepSize`
        """
        res = []
        num = max(1, int(self.duration / stepSize))  # if smaller still take it
        for i in range(num):
            newE = self.copy()
            newE.startTime = self.startTime + i * stepSize
            newE.duration = stepSize
            res += [newE]
        return res

    def containsTime(self, time):
        """Return true if event is active at given time

        Args:
            time: float
                time to compare with
        """
        return (time >= self.startTime) and (time < self.startTime + self.duration)


class Pattern(object):
    """
    Class representing a pattern (i.e. collection of events).
    Holds a list of events and provides basic manipulation functions.

    Parameters
    ----------
    duration: float
        length of pattern. Usually in beats, but time scale is up to
        the user (it can be useful if working on 32th note steps).
    events: list
        list of Event for this pattern.
    bpm: float
        initial tempo in beats per minute for this pattern (default: 120).
    timeSignature: list of ints [i,i]
        list of integers representing the time signature as [numerator, denominator].
     startTime: float
        startTime of pattern (useful when splitting in sub patterns).
     viewPoints: dict
        dict of ViewPoints

    """

    def __init__(self,
                 duration=0,
                 events=None,
                 bpm=120,
                 timeSignature=(4, 4),  # changed list to tuple.
                 key="C",
                 originFilePath="",
                 name=""):
        self.duration = duration
        if events:
            self.events = events
        else:
            self.events = []
        self.viewpoints = {}
        self.bpm = bpm
        self.timeSignature = timeSignature
        self.key = key
        self.originFilePath = originFilePath
        self.name = name
        self.startTime = 0
        self.originPattern = None

    def __repr__(self):
        """
        Print out the list of events.

        Notes
        -----
        Each line represents an event formatted as '[tag] pitch velocity startTime duration'

        """
        s = "Pattern %s: duration: %.2f,bpm: %.2f,time signature: %d/%d\n" % (self.name,
                                                                              self.duration,
                                                                              self.bpm,
                                                                              self.timeSignature[0],
                                                                              self.timeSignature[1])
        for e in self.events:
            s += str(e) + "\n"
        return s

    def __len__(self):
        return len(self.events)

    def __getitem__(self, index):
        """
        Utility to access events as list member: Pattern[idx] = Pattern.events[idx]

        """
        return self.events[index]

    def __eq__(self, other):
        if isinstance(other, Pattern):
            return (self.events == other.events) and (self.duration == other.duration) and (
                self.timeSignature == other.timeSignature) and (self.startTime == other.startTime)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __setitem__(self, index, item):
        self.events[index] = item

    def applyLegato(self, usePitchValues=False):
        """
        This function supress the possible silences in this pattern by
        stretching consecutive identical events (tags or pitch numbers).

        Parameters
        ----------
        usePitchValues: boolean
            use pitch note numbers instead of tags (it is a bit faster).

        """

        def _perVoiceLegato(pattern):

            pattern.reorderEvents()
            if len(pattern) == 0:
                patternLog.warning("try to apply legato on an empty voice")

                return
            for idx in range(1, len(pattern)):

                diff = pattern[idx].startTime - pattern[idx - 1].getEndTime()
                if diff > 0:
                    pattern[idx - 1].duration += diff

            diff = pattern.duration - pattern[-1].getEndTime()
            if diff > 0:
                pattern[-1].duration += diff

        if usePitchValues:
            for p in self.getAllPitches():
                voice = self.getPatternWithPitch(p)
                _perVoiceLegato(voice)
        for t in self.getAllTags():
            voice = self.getPatternWithTags(tagToLookFor=t, exactSearch=False, makeCopy=False)
            _perVoiceLegato(voice)

    def transpose(self, interval):
        """
        Transposes a Pattern to the desired interval

        Parameters
        ----------
        interval: int
            transposition factor in semitones (positive or negative int)

        """
        for e in self.events:
            e.pitch += interval
            e.tag = [gsutil.pitch2name(e.pitch, gsdefs.pitchNames)]
            # return self

    def setDurationFromLastEvent(self, onlyIfBigger=True):
        """Sets duration to last event NoteOff

        Parameters
        ----------
        onlyIfBigger: bool
            update duration only if last Note off is bigger

        Notes
        -----
        If inner events have a bigger time span than self.duration,
        increase the duration to fit.

        """
        total = self.getLastNoteOff()
        if total and (total > self.duration or not onlyIfBigger):
            self.duration = total

    def reorderEvents(self):
        """
        Ensure than our internal event list `events` is time sorted.
        It can be useful for time sensitive events iteration.

        """
        self.events.sort(key=lambda x: x.startTime, reverse=False)

    def getLastNoteOff(self):
        """
        Gets last event end time

        Returns
        -------
        lastNoteOff: float
             The time corresponding to the end of the last event.

        """
        if len(self.events):
            self.reorderEvents()
            return self.events[-1].duration + self.events[-1].startTime
        else:
            return None

    def addEvent(self, event):
        """
        Add an event increasing its duration if needed.

        Args:
            event: the Event to be added
        """
        self.events += [event]
        self.setDurationFromLastEvent()

    def removeEvent(self, event):
        """remove given event
        Args:
            event: the Event to be added
        """
        idxToRemove = []
        idx = 0
        for e in self.events:
            if event == e:
                idxToRemove += [idx]
            idx += 1

        for i in idxToRemove:
            del self.events[i]

    def removeByTags(self, tags):
        """Remove all event(s) in a pattern with specified tag(s).

        Args:
            tags: list of tag(s)
        """
        for e in self.events:
            if e.hasOneOfTags(tuple(tags)):
                self.removeEvent(e)

    def quantize(self, stepSize, quantizeStartTime=True, quantizeDuration=True):
        """ Quantize events.

        Args:
            stepSize: the duration that we want to quantize to
            quantizeDuration: do we quantize duration?
            quantizeStartTime: do we quantize startTimes
        """
        beatDivision = 1.0 / stepSize
        if quantizeStartTime and quantizeDuration:
            for e in self.events:
                e.startTime = int(e.startTime * beatDivision) * 1.0 / beatDivision
                e.duration = int(e.duration * beatDivision) * 1.0 / beatDivision
        elif quantizeStartTime:
            for e in self.events:
                e.startTime = int(e.startTime * beatDivision) * 1.0 / beatDivision
        elif quantizeDuration:
            for e in self.events:
                e.duration = int(e.duration * beatDivision) * 1.0 / beatDivision

    def timeStretch(self, ratio):
        """Time-stretch a pattern.

        Args:
            ratio: the ratio used for time stretching
        """
        for e in self.events:
            e.startTime *= ratio
            e.duration *= ratio
        self.duration *= ratio

    def getStartingEventsAtTime(self, time, tolerance=0):
        """ Get all events activating at a given time.

        Args:
            time: time asked for
            tolerance: allowed deviation of start time
        Returns:
            list of events
        """
        res = []
        for e in self.events:
            if (time - e.startTime >= 0 and time - e.startTime <= tolerance):
                res += [e]
        return res

    def getActiveEventsAtTime(self, time, tolerance=0):  # todo: either implement or remove tolerance
        """ Get all events currently active at a givent time.

        Args:
            time: time asked for
            tolerance: admited deviation of start time
        Returns:
            list of events
        """
        res = []
        for e in self.events:
            if (time - e.startTime >= 0 and time - e.startTime < e.duration):
                res += [e]
        return res

    def copy(self):
        """Deepcopy a pattern
        """
        return copy.deepcopy(self)

    def getACopyWithoutEvents(self):
        """Copy all fields but events.
            Useful for creating patterns from patterns.
        """
        p = Pattern()
        p.duration = self.duration
        p.bpm = self.bpm
        p.timeSignature = self.timeSignature
        p.originFilePath = self.originFilePath
        p.name = self.name
        return p

    def getAllTags(self):
        """ Returns all used tags in this pattern.

        Returns:
            set of tags composed of all possible tags
        """
        tagsList = []
        for e in self.events:
            tagsList += [e.tag]
        tagsList = set(tagsList)
        return tagsList

    def getAllPitches(self):
        """ Returns all used pitch in this pattern.

        Returns:
            list of integers composed of all pitches present in this pattern
        """
        pitchs = []
        for e in self.events:
            pitchs += [e.pitch]
        pitchs = list(set(pitchs))
        return pitchs

    def getPatternWithTags(self, tagToLookFor, exactSearch=True, makeCopy=True):
        """Returns a sub-pattern with the given tags.

        Args:
            tagToLookFor: tag,tags list or lambda  expression (return boolean based on tag input): tags to be checked for
            exactSearch: bool: if True the tags argument can be an element of tag to look for, example : if we set tags='maj',an element with tag ('C','maj') will be valid
            makeCopy: do we return a copy of original events (avoid modifying originating events when modifying the returned subpattern)
        Returns:
            a Pattern with only events that tags corresponds to given tagToLookFor
        """
        if isinstance(tagToLookFor, list):
            if exactSearch:
                patternLog.error("cannot search exactly with a list of elements")
            boolFunction = lambda inTags: len(inTags) > 0 and inTags in tagToLookFor
        elif callable(tagToLookFor):
            boolFunction = tagToLookFor
        else:
            # tuple / string or any hashable object
            if exactSearch:
                boolFunction = lambda inTags: inTags == tagToLookFor
            else:
                boolFunction = lambda inTags: (inTags == tagToLookFor) or (len(inTags) > 0 and tagToLookFor in inTags)

        res = self.getACopyWithoutEvents()
        for e in self.events:
            found = boolFunction(e.tag)
            if found:
                newEv = e if not makeCopy else e.copy()
                res.events += [newEv]
        return res

    def getPatternWithPitch(self, pitch, makeCopy=True):
        """Returns a sub-pattern with the given pitch.

        Args:
            pitch: pitch to look for
            makeCopy: do we return a copy of original events (avoid modifying originating events when modifying the returned subpattern)
        Returns:
            a Pattern with only events that pitch corresponds to given pitch
        """
        res = self.getACopyWithoutEvents()
        for e in self.events:
            found = (e.pitch == pitch)
            if found:
                newEv = e if not makeCopy else e.copy()
                res.events += [newEv]

        return res

    def getPatternWithoutTags(self, tagToLookFor, exactSearch=False, makeCopy=True):
        """Returns a sub-pattern without the given tags.

        Args:
            tagToLookFor: tag or tag list: tags to be checked for
            exactSearch: bool: if True the tags have to be exactly the same as tagToLookFor, else they can be included in events tag
            makeCopy: do we return a copy of original events (avoid modifying originating events when modifying the returned subpattern)

        Returns:
            a Pattern with events without given tags
        """

        if isinstance(tagToLookFor, list):
            if exactSearch:
                patternLog.error("cannot search exactly with a list of elements")
            boolFunction = lambda inTags: len(inTags) > 0 and inTags in tagToLookFor
        elif callable(tagToLookFor):
            boolFunction = tagToLookFor
        else:
            # tuple / string or any hashable object
            if exactSearch:
                boolFunction = lambda inTags: inTags == tagToLookFor
            else:
                boolFunction = lambda inTags: (inTags == tagToLookFor) or (len(inTags) > 0 and tagToLookFor in inTags)

        res = self.getACopyWithoutEvents()
        for e in self.events:
            needToExclude = boolFunction(e.tag)
            if not needToExclude:
                newEv = e if not makeCopy else e.copy()
                res.events += [newEv]
        return res

    def alignOnGrid(self, stepSize, repeatibleTags=['silence']):
        """Align this pattern on a temporal grid.
        Very useful to deal with step-sequenced pattern:
        - all events durations are shortened to stepsize
        - all events startTimes are quantified to stepsize

        RepeatibleTags allow to deal with `silences type` of events:
        - if a silence spread over integration than one stepsize, we generate an event for each stepSize

        Thus each step is ensured to be filled with one distinct event at least.

        Args:
            stepSize: temporal definition of the grid
            repeatibleTags: tags
        """
        newEvents = []
        for e in self.events:
            if e.tagIs(repeatibleTags):
                evToAdd = e.cutInSteps(stepSize)
            else:
                evToAdd = [e]
            for ea in evToAdd:
                ea.startTime = int(ea.startTime / stepSize + 0.5) * stepSize
                # avoid adding last event out of duration range
                if ea.startTime < self.duration:
                    ea.duration = stepSize
                    newEvents += [ea]

        self.events = newEvents
        self.removeOverlapped()
        return self

    def removeOverlapped(self, usePitchValues=False):
        """Remove overlapped elements.

            Args:
                usePitchValues: use pitch to discriminate events
        """
        self.reorderEvents()
        newList = []
        idx = 0
        for e in self.events:
            found = False
            overLappedEv = []
            for i in range(idx + 1, len(self.events)):
                ee = self.events[i]
                if usePitchValues:
                    equals = (ee.pitch == e.pitch)
                else:
                    equals = (ee.tag == e.tag)
                if equals:
                    if (ee.startTime >= e.startTime) and (ee.startTime < e.startTime + e.duration):
                        found = True
                        if ee.startTime - e.startTime > 0:
                            e.duration = ee.startTime - e.startTime
                            newList += [e]
                            overLappedEv += [ee]
                        else:
                            patternLog.info("strict overlapping of start times %s with %s" % (e, ee))

                if ee.startTime > (e.startTime + e.duration):
                    break
            if not found:
                newList += [e]
            else:
                patternLog.info("remove overlapping %s with %s" % (e, overLappedEv))
            idx += 1
        self.events = newList
        # return self

    def getAllIdenticalEvents(self, event, allTagsMustBeEquals=True):
        """Get a list of event with same tags.

        Args:
            event:event to compare with
            allTagsMustBeEquals: shall we get exact tags equality or be fine with one common tag (valable if tags are tuple)

        Returns:
            list of events that have all or one tags in common
        """
        res = []
        for e in self.events:
            equals = False
            equals = event.allTagsAreEqualWith(e) if allTagsMustBeEquals else event.hasOneCommonTagWith(e)
            if equals:
                res += [e]

    def getFilledWithSilences(self, maxSilenceTime=0, perTag=False, silenceTag='silence'):
        pattern = self.copy()
        pattern.fillWithSilences(maxSilenceTime=maxSilenceTime, perTag=perTag, silenceTag=silenceTag)
        return pattern

    def fillWithSilences(self, maxSilenceTime=0, perTag=False, silenceTag='silence', silencePitch=0):
        """Fill empty time intervals (i.e no event) with silence event.

        Args:
            maxSilenceTime: if positive value is given, will add multiple silence of maxSilenceTime for empty time larger than maxSilenceTime
            perTag: fill silence for each Tag
            silenceTag: tag that will be used when inserting the silence event
            silencePitch : the desired pitch of new silences events
        """
        self.reorderEvents()

        def _fillListWithSilence(pattern, silenceTag, silencePitch=-1):
            lastOff = 0
            newEvents = []

            for e in pattern.events:
                if e.startTime > lastOff:
                    if maxSilenceTime > 0:
                        while e.startTime - lastOff > maxSilenceTime:
                            newEvents += [Event(lastOff, maxSilenceTime, silencePitch, 0, silenceTag)]
                            lastOff += maxSilenceTime
                    newEvents += [Event(lastOff, e.startTime - lastOff, silencePitch, 0, silenceTag)]
                newEvents += [e]
                lastOff = max(lastOff, e.startTime + e.duration)

            if lastOff < pattern.duration:
                if maxSilenceTime > 0:
                    while lastOff < pattern.duration - maxSilenceTime:
                        newEvents += [Event(lastOff, maxSilenceTime, silencePitch, 0, silenceTag)]
                        lastOff += maxSilenceTime
                newEvents += [Event(lastOff, pattern.duration - lastOff, silencePitch, 0, silenceTag)]
            return newEvents

        if not perTag:
            self.events = _fillListWithSilence(self, silenceTag, silencePitch)
        else:
            allEvents = []
            for t in self.getAllTags():
                allEvents += _fillListWithSilence(
                        self.getPatternWithTags(tagToLookFor=t, exactSearch=False, makeCopy=False), silenceTag,
                        silencePitch)
            self.events = allEvents

    def fillWithPreviousEvent(self):
        """
        Fill gaps between onsets making longer the duration of the previous event.
        """
        onsets = []
        for e in self.events:
            if e.startTime not in onsets:
                onsets.append(e.startTime)
        onsets.append(self.duration)

        for e in self.events:
            e.duration = onsets[onsets.index(e.startTime) + 1] - e.startTime

    def getPatternForTimeSlice(self, startTime, length, trimEnd=True):
        """Returns a pattern within given timeslice.

        Args:
            startTime: start time for time slice
            length: length of time slice
            trimEnd: cut any events that ends after startTime + length
        Returns:
            a new GSpattern within time slice
        """
        p = self.getACopyWithoutEvents()
        p.startTime = startTime
        p.duration = length
        for e in self.events:
            if 0 <= (e.startTime - startTime) < length:
                newEv = e.copy()
                newEv.startTime -= startTime
                p.events += [newEv]
        if trimEnd:
            for e in p.events:
                toCrop = e.startTime + e.duration - length
                if toCrop > 0:
                    e.duration -= toCrop
        return p

    def toJSONDict(self, useTagIndexing=True):
        """Gives a standard dict for json output.
        Args:
        useTagIndexing: if true, tags are stored as indexes from a list of all tags (reduce size of json files)
        """
        res = {}
        self.setDurationFromLastEvent()
        res['name'] = self.name
        if self.originPattern: res['originPattern'] = self.originPattern.name
        res['timeInfo'] = {'duration': self.duration, 'bpm': self.bpm, 'timeSignature': self.timeSignature}
        res['eventList'] = []
        res['viewpoints'] = {k: v.toJSONDict(useTagIndexing) for k, v in self.viewpoints.items()}
        if useTagIndexing:
            allTags = self.getAllTags()
            res['eventTags'] = allTags

            def findIdxforTags(tags, allTags):
                return [allTags.index(x) for x in tags]

            for e in self.events:
                res['eventList'] += [{'on':       e.startTime,
                                      'duration': e.duration,
                                      'pitch':    e.pitch,
                                      'velocity': e.velocity,
                                      'tagIdx':   findIdxforTags(e.tag, allTags)
                                      }]
        else:
            for e in self.events:
                res['eventList'] += [{'on':       e.startTime,
                                      'duration': e.duration,
                                      'pitch':    e.pitch,
                                      'velocity': e.velocity,
                                      'tag':      e.tag
                                      }]

        return res

    def fromJSONDict(self, json, parentPattern=None):
        """Loads a json API dict object to this pattern

        Args:
            json: a dict created from reading json file with GS API JSON format
        """
        self.name = json['name']
        self.duration = json['timeInfo']['duration']
        self.bpm = json['timeInfo']['bpm']
        self.timeSignature = tuple(json['timeInfo']['timeSignature'])
        if 'originPattern' in json:
            def findOriginPatternInParent(name):
                if not name:
                    return None
                checkedPattern = parentPattern
                while checkedPattern:
                    if checkedPattern.name == name:
                        return checkedPattern
                    checkedPattern = checkedPattern.originPattern

                assert False, "no origin pattern found"

            self.originPattern = findOriginPatternInParent(json['originPattern'])

        hasIndexedTags = 'eventTags' in json.keys()
        if hasIndexedTags:
            tags = json['eventTags']
            for e in json['eventList']:
                self.events += [Event(startTime=e['on'],
                                      duration=e['duration'],
                                      pitch=e['pitch'],
                                      velocity=e['velocity'],
                                      tag=tuple([tags[f] for f in e['tagsIdx']])
                                      )]
        else:
            for e in json['eventList']:
                self.events += [Event(startTime=e['on'],
                                      duration=e['duration'],
                                      pitch=e['pitch'],
                                      velocity=e['velocity'],
                                      tag=e['tag']
                                      )]

        self.viewpoints = {k: Pattern().fromJSONDict(v, parentPattern=self) for k, v in json['viewpoints'].items()}
        self.setDurationFromLastEvent()

        return self

    def splitInEqualLengthPatterns(self, desiredLength, viewpointName=None, makeCopy=True, supressEmptyPattern=True):
        """Splits a pattern in consecutive equal length cuts.

        Args:
            desiredLength: length desired for each pattern
            viewpointName : if given, slice the underneath viewpoint instead
            makeCopy: returns a distint copy of original pattern events, if you don't need original pattern anymore setting it to False will increase speed

        Returns:
            a list of patterns of length desiredLength
        """

        def _handleEvent(e, patterns, makeCopy):
            p = int(math.floor(e.startTime * 1.0 / desiredLength))
            numPattern = str(p)
            if numPattern not in patterns:
                patterns[numPattern] = patternToSlice.getACopyWithoutEvents()
                patterns[numPattern].startTime = p * desiredLength
                patterns[numPattern].duration = desiredLength
                patterns[numPattern].name = patternToSlice.name + "_" + numPattern
            newEv = e if not makeCopy else e.copy()

            if newEv.startTime + newEv.duration > (p + 1) * desiredLength:
                remainingEvent = e.copy()
                newOnset = (p + 1) * desiredLength
                remainingEvent.duration = remainingEvent.getEndTime() - newOnset
                remainingEvent.startTime = newOnset
                _handleEvent(remainingEvent, patterns, makeCopy)
                newEv.duration = (p + 1) * desiredLength - e.startTime

            newEv.startTime -= p * desiredLength
            patterns[numPattern].events += [newEv]

        patterns = {}

        patternToSlice = self.viewpoints[viewpointName] if viewpointName else self
        for e in patternToSlice.events:
            _handleEvent(e, patterns, makeCopy)
        res = []
        maxListLen = int(math.ceil(patternToSlice.duration * 1.0 / desiredLength))
        for p in range(maxListLen):
            pName = str(p)
            if pName in patterns:
                curPattern = patterns[pName]
                curPattern.setDurationFromLastEvent()
            else:
                curPattern = None
            if (not supressEmptyPattern) or curPattern:
                res += [curPattern]
        return res

    def generateViewpoint(self, name, descriptor=None, sliceType=None):
        """
        generate viewpoints in this Pattern
        Args:
            name: name of the viewpoint generated , if name is one of ["chords",] it will generate the default descriptor
            descriptor : if given it's the descriptor used
            sliceType: type of slicing to compute viewPoint:
                if integer its duration based see:splitInEqualLengthPatterns
                if "perEvent" generates new pattern every new events startTime,
                if "all" get the whole pattern (generate one and only viewPoint value)
        """

        def _computeViewpoint(originPattern, descriptor, name, sliceType=1):
            """
            Internal function for computing viewPoint

            """
            viewpoint = originPattern.getACopyWithoutEvents()
            viewpoint.name = name
            viewpoint.originPattern = originPattern

            if isinstance(sliceType, int):
                step = sliceType
                patternsList = originPattern.splitInEqualLengthPatterns(step)

            elif sliceType == "perEvent":
                originPattern.reorderEvents()
                lastTime = -1
                patternsList = []
                for consideredEvent in originPattern:
                    if lastTime < consideredEvent.startTime:  # group all identical startTimeEvents
                        pattern = originPattern.getACopyWithoutEvents()
                        pattern.startTime = consideredEvent.startTime
                        pattern.events = originPattern.getActiveEventsAtTime(consideredEvent.startTime)
                        pattern.duration = 0

                        for se in pattern.events:
                            # TODO do we need to trim to beginning?
                            # some events can have negative startTimes and each GSpattern.duration corresponds to difference between consideredEvent.startTime and lastEvent.startTime (if some events were existing before start of consideredEvent)
                            #     se.startTime-=consideredEvent.startTime
                            eT = se.getEndTime() - pattern.startTime
                            if eT > pattern.duration:
                                pattern.duration = eT
                        lastTime = consideredEvent.startTime

                        patternsList += [pattern]

            elif sliceType == "all":
                patternsList = [originPattern]
            else:
                patternLog.error("sliceType %s not valid" % (sliceType))
                assert False

            for subPattern in patternsList:
                if subPattern:
                    viewpoint.events += [Event(duration=subPattern.duration,
                                               startTime=subPattern.startTime,
                                               tag=descriptor.getDescriptorForPattern(subPattern),
                                               originPattern=subPattern)]

            return viewpoint

        if descriptor:
            self.viewpoints[name] = _computeViewpoint(originPattern=self,
                                                      descriptor=descriptor,
                                                      sliceType=sliceType,
                                                      name=name)
        else:
            if name == "chords":
                from .descriptors.chord import Chord
                self.viewpoints[name] = _computeViewpoint(originPattern=self,
                                                          descriptor=Chord(),
                                                          sliceType=4,
                                                          name=name)
        # can use it as a return value
        return self.viewpoints[name]

    def printASCIIGrid(self, blockSize=1):
        def __areSilenceEvts(l):
            if len(l) > 0:
                for e in l:
                    if 'silence' not in e.tag:
                        return False
            return True

        for t in self.getAllTags():
            noteOnASCII = '|'
            sustainASCII = '>'
            silenceASCII = '-'
            out = "["
            p = self.getPatternWithTags(t, makeCopy=True)  # .alignOnGrid(blockSize);
            # p.fillWithSilences(maxSilenceTime = blockSize)
            isSilence = __areSilenceEvts(p.getActiveEventsAtTime(0))
            inited = False
            lastActiveEvent = p.events[0]
            numSteps = int(self.duration * 1.0 / blockSize)

            for i in range(numSteps):
                time = i * 1.0 * blockSize
                el = p.getActiveEventsAtTime(time)
                newSilenceState = __areSilenceEvts(el)
                if newSilenceState != isSilence:
                    if newSilenceState:
                        out += silenceASCII
                    else:
                        out += noteOnASCII
                        lastActiveEvent = el[0]
                elif newSilenceState:
                    out += silenceASCII
                elif not newSilenceState:
                    if el[0].startTime == lastActiveEvent.startTime:
                        out += sustainASCII
                    else:
                        out += noteOnASCII
                        lastActiveEvent = el[0]

                isSilence = newSilenceState
                inited = True

            out += "]: " + t
            print(out)


class Dataset(object):
    """
    Class that holds a list of patterns imported from a specific gpath in glob
    style.

    """
    defaultMidiFolder = os.path.abspath(__file__ + "../examples/corpora/drums/")
    defaultMidiGlob = "*.mid"

    def __init__(self, midiFolder=defaultMidiFolder, midiGlob=defaultMidiGlob,
                 midiMap=gsdefs.simpleDrumMap, checkForOverlapped=True):

        self.midiFolder = midiFolder
        self.setMidiGlob(midiGlob)
        self.midiMap = midiMap
        self.checkForOverlapped = checkForOverlapped
        self.importMIDI()

    def setMidiGlob(self, globPattern):

        import glob
        if '.mid' in globPattern[-4:]:
            globPattern = globPattern[:-4]
        self.midiGlob = globPattern + '.mid'
        self.globPath = os.path.abspath(os.path.join(self.midiFolder, self.midiGlob))
        self.files = glob.glob(self.globPath)
        if len(self.files) == 0:
            patternLog.error("no files found for path: " + self.globPath)
        else:
            self.idx = random.randint(0, len(self.files) - 1)

    def getAllSliceOfDuration(self, desiredDuration, viewpointName=None, supressEmptyPattern=True):
        res = []
        for p in self.patterns:
            res += p.splitInEqualLengthPatterns(viewpointName=viewpointName,
                                                desiredLength=desiredDuration,
                                                supressEmptyPattern=supressEmptyPattern)
        return res

    def generateViewpoint(self, name, descriptor=None, sliceType=None):
        for p in self.patterns:
            p.generateViewpoint(name=name, descriptor=descriptor, sliceType=sliceType)

    def importMIDI(self, fileName=""):

        if fileName:
            self.setMidiGlob(fileName)

        self.patterns = []

        for p in self.files:
            patternLog.info('using ' + p)
            p = gsio.fromMidi(p, self.midiMap, tracksToGet=[], checkForOverlapped=self.checkForOverlapped)
            self.patterns += [p]

        return self.patterns

    def __getitem__(self, index):
        """Utility to access paterns as list member: GSDataset[idx] = GSDataset.patterns[idx]
        """
        return self.patterns[index]


class PatternMarkov(object):
    """
    Computes a Markov chain from pattern.

    Args:
        order: order used for markov computation
        numSteps: number of steps to consider (binarization of pattern)

    Attributes:
        order: order used for markov computation
        numSteps: number of steps to consider (binarization of pattern)
    """

    def __init__(self, order=1, numSteps=32, loopDuration=4, ):
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
            patternLog.error("PatternMarkov need a list")
            return False
        else:
            self.originPatterns = patternClasses
            self.buildTransitionTable()

    def getMarkovConfig(self):
        return "order(%i), loopLength(%f), numSteps(%i)" % (self.order, self.loopDuration, self.numSteps)

    def buildTransitionTable(self):
        """ builds transision table for the previously given list of Pattern
        """
        self.transitionTable = [{} for f in range(int(self.numSteps))]

        self.binarizedPatterns = copy.deepcopy(self.originPatterns)
        for p in self.binarizedPatterns:
            self.formatPattern(p)
            self.checkSilences(p)
            if (self.numSteps != int(p.duration)):
                patternLog.warning("PatternMarkov : quantization to numSteps failed, numSteps=" + str(
                        self.numSteps) + " duration=" + str(p.duration) + " cfg : " + self.getMarkovConfig())
            for step in range(self.numSteps):
                l = [p.getStartingEventsAtTime(step)]
                self.checkSilenceInList(l)
                curEvent = self._buildTupleForEvents(l)[0]
                combinationName = self._buildTupleForEvents(self.getLastEvents(p, step, self.order, 1));

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
                patternLog.error("wrong transition table, zero state for " + str(previousTags))
                patternLog.error(str(self.transitionTable[step]))
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
                    patternLog.error("not found combination %s at step %i \n transitions\n %s" % (
                        ','.join(newPast), i, self.transitionTable[i]))
                    raise Exception(" can't find combination in markov")
                else:
                    patternLog.warning("not found combination %s " % (','.join(newPast)))

        pattern = Pattern()
        idx = 0

        stepSize = 1.0 * self.loopDuration / self.numSteps

        for el in events:
            for tagElem in el:
                if tagElem != 'silence':
                    pattern.events += [Event(idx * stepSize, stepSize, 100, 127, tag=tagElem)]

            idx += 1
        pattern.duration = self.loopDuration

        return pattern

    def checkSilences(self, p):
        for i in range(int(p.duration)):
            c = p.getStartingEventsAtTime(i)
            if len(c) > 1 and ("silence" in c):
                patternLog.error("wrong silence")

    def checkSilenceInList(self, c):
        if len(c) > 1 and ('silence' in c):
            patternLog.error("wrong silence")

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
        res = {"transitionTable": self.transitionTable, "order": self.order, "numSteps": self.numSteps,
               "loopDuration":    self.loopDuration}
        return res

    def setInternalState(self, state):
        """utility function to load current state
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
        return list(set(self.getPossibleInStatesAtStep(step) + self.getPossibleOutStatesAtStep(step)))

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

    def getMatrixAtStep(self, step, possibleStatesIn=None, possibleStatesOut=None, matrix=None):
        if step < 0: step += len(self.transitionTable)
        possibleStatesIn = possibleStatesIn or self.getPossibleInStatesAtStep(step)
        possibleStatesOut = possibleStatesOut or self.getPossibleOutStatesAtStep(step)
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
        mat, labelsIn, labelsOut = self.getMatrixAtStep(step)  # ,possibleStates = allTags)
        self.__plotMatrix(mat, labelsIn, labelsOut)

    def plotGlobalMatrix(self):
        numSteps = len(self.transitionTable)
        possibleStatesIn = list(
                set([item for step in range(numSteps) for item in self.getPossibleInStatesAtStep(step)]))
        possibleStatesOut = list(
                set([item for step in range(numSteps) for item in self.getPossibleOutStatesAtStep(step)]))
        sizeIn = len(possibleStatesIn)
        sizeOut = len(possibleStatesOut)

        matrix = [[0] * sizeOut for i in range(sizeIn)]
        for step in range(numSteps):
            self.getMatrixAtStep(step, possibleStatesIn=possibleStatesIn, possibleStatesOut=possibleStatesOut,
                                 matrix=matrix)
        self.__plotMatrix(matrix, possibleStatesIn, possibleStatesOut)


def patternToList(pattern):
    """
    Converts a pattern to a regular python list.

    """
    list_of_events = []
    for event in pattern.events:
        list_of_events.append([event.pitch, event.startTime, event.duration])
    return list_of_events
