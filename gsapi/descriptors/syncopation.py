#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from math import ceil

from .base_descriptor import *


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
            self.noteGrid[i] = len(pattern.getActiveEventsAtTime(i))

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
