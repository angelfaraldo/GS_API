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

    """
    defaultMidiFolder = os.path.abspath(__file__ + "../examples/corpora/harmony/")
    defaultMidiGlob = "*.mid"

    def __init__(self, midiFolder=defaultMidiFolder, midiGlob=defaultMidiGlob,
                 midiMap=gsdefs.simpleDrumMap, checkForOverlapped=True):
        self.patterns = None
        self.midiGlob = None
        self.globPath = None
        self.files = None
        self.idx = None
        self.midiFolder = midiFolder
        self.setMidiGlob(midiGlob)
        self.midiMap = midiMap
        self.checkForOverlapped = checkForOverlapped
        self.importMIDI()

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

    def importMIDI(self, fileName=""):
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
