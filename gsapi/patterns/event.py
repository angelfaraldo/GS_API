from __future__ import absolute_import, division, print_function

import collections
import copy

import logging
patternLog = logging.getLogger("gsapi.Event")  # logger for Event related operations


class Event(object):
    """Represents an event of a pattern with startTime, duration, pitch,
    velocity and tag variables.

    Class variables:
        startTime: startTime of event
        duration: duration of event
        pitch: pitch of event
        velocity: velocity of event
        tag: any hashable object representing the event , i.e strings, tuples, objects (but not lists)
        originPattern: keeps track of origin pattern for events generated from pattern,
        for example, a chord event can still access to its individual components
        via originPattern (see Pattern.generateViewpoints)
    """
    def __init__(self, startTime=0, duration=1, pitch=60, velocity=80, tag=None, originPattern=None):
        self.duration = duration
        self.startTime = startTime

        self.originPattern = originPattern
        if not tag:
            self.tag = ()
        elif isinstance(tag, list):
            patternLog.error("tag cannot be list, converting to tuple")
            self.tag = tuple(tag)

        elif not isinstance(tag, collections.Hashable):
            patternLog.error("tag has to be hashable, trying conversion to tuple")
            self.tag = (tag,)
        else:
            self.tag = tag

        self.pitch = pitch
        self.velocity = velocity

    def __repr__(self):
        return "%s %i %i %05.4f %05.4f" % (self.tag,
                                           self.pitch,
                                           self.velocity,
                                           self.startTime,
                                           self.duration)

    def __eq__(self, other):
        if isinstance(other, Event):
            return (self.startTime == other.startTime) and (self.pitch == other.pitch) \
                   and (self.velocity == other.velocity) and (self.duration == other.duration) \
                   and (self.tag == other.tag)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def hasOneCommonTagWith(self, event):
        """Compare tags between events

        Args:
            event: event to compare with
        Returns:
            True if at least one tag is equal
        """
        # if type(self.tag)!=type(event.tag):
        #     return False
        return self.hasOneOfTags(event.tag)

    def hasOneOfTags(self, tags):
        """Compare this event's tags with a list of possible tag.

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
            time: time to compare with
        """
        return (time >= self.startTime) and (time < self.startTime + self.duration)
