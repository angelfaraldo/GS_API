#!/usr/bin/env python
# encoding: utf-8
"""
The dataset module contains the Dataset class, which allows to load multiple
files at once.

"""

from __future__ import absolute_import, division, print_function

import glob
import os
import random

from . import gsio, gsdefs

import logging
gsdatasetLog = logging.getLogger("gsapi.gsdataset")

gsdatasetLog.setLevel(level=logging.WARNING)


class Dataset(object):
    """
    Class that holds a list of patterns imported
    from a specific gpath in glob style.

    Parameters
    ----------
    midiFolder: float
        startTime of the Event.
    duration: float
        duration of Event.
    pitch: int
        pitch of the Event in midi note numbers.
    velocity: int
        velocity of event in midi format (0-127).
    tag: string, tuple, object
        any hashable object representing the event, except lists.
    originPattern: Pattern
        keeps track of origin pattern for events generated from pattern,
        e.g., a chord event can still access to its individual components
        via originPattern (see Pattern.generateViewpoints)

    """
    def __init__(self, midiFolder="", midiGlob="*.mid",
                 midiMap=gsdefs.simpleDrumMap, checkForOverlapped=True):
        self.midiFolder = midiFolder
        self.midiGlob = None
        self.midiMap = midiMap
        self.checkForOverlapped = checkForOverlapped

        self.patterns = None
        self.globPath = None
        self.files = None
        self.idx = None
        self.setMidiGlob(midiGlob)
        self.importMidi()

    def setMidiGlob(self, globPattern):
        if '.mid' in globPattern[-4:]:
            globPattern = globPattern[:-4]
        self.midiGlob = globPattern + '.mid'
        self.globPath = os.path.abspath(
            os.path.join(self.midiFolder, self.midiGlob))
        self.files = glob.glob(self.globPath)
        if len(self.files) == 0:
            gsdatasetLog.error("no files found for path: " + self.globPath)
        else:
            self.idx = random.randint(0, len(self.files) - 1)

    def getAllSliceOfDuration(self, desiredDuration, viewpointName=None,
                              supressEmptyPattern=True):
        res = []
        for p in self.patterns:
            res += p.splitInEqualLengthPatterns(viewpointName=viewpointName,
                                                desiredLength=desiredDuration,
                                                supressEmptyPattern=supressEmptyPattern)
        return res

    def generateViewpoint(self, name, descriptor=None, sliceType=None):
        for p in self.patterns:
            p.generateViewpoint(name=name, descriptor=descriptor,
                                sliceType=sliceType)

    def importMidi(self, fileName=""):
        if fileName:
            self.setMidiGlob(fileName)
        self.patterns = []
        for p in self.files:
            gsdatasetLog.info('using ' + p)
            p = gsio.fromMidi(p, self.midiMap, tracksToGet=[],
                              checkForOverlapped=self.checkForOverlapped)
            self.patterns += [p]
        return self.patterns

    def __getitem__(self, index):
        """
        Utility to access paterns as list member:
        Dataset[idx] = Dataset.patterns[idx]

        """
        return self.patterns[index]
