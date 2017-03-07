from __future__ import absolute_import, division, print_function

import logging
import os
import random

from . import utils
from .. import io

datasetLog = logging.getLogger("gsapi.Dataset")


class Dataset(object):
    """Helper to hold a list of patterns imported from specific gpath (glob style)"""

    defaultMidiFolder = os.path.abspath(__file__ + "../../../../corpora/drums/")
    defaultMidiGlob = "*.mid"

    def __init__(self,
                 midiFolder=defaultMidiFolder,
                 midiGlob=defaultMidiGlob,
                 midiMap=utils.simpleDrumMap,
                 checkForOverlapped=True):

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
            datasetLog.error("no files found for path: " + self.globPath)
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
            datasetLog.info('using ' + p)
            p = io.fromMidi(p, self.midiMap, tracksToGet=[], checkForOverlapped=self.checkForOverlapped)
            self.patterns += [p]

        return self.patterns

    def __getitem__(self, index):
        """Utility to access paterns as list member: GSDataset[idx] = GSDataset.patterns[idx]
        """
        return self.patterns[index]
