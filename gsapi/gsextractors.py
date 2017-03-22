#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

import os
import sys

from gsapi.descriptors.density import Density
from gsapi.descriptors.number_of_tags import NumberOfTags
from gsapi.gsdataset import Dataset


class DensityDrumSpace:
        # #Descriptor1: number of instruments

        # listofinstruments=[]
        # for steps in pattern:
        # 	for events in steps:
        # 		listofinstruments.append(events)
        # setofinstruments=list(set(listofinstruments))
        # setofinstruments.remove(0)
        # noi=len(setofinstruments)
        # descriptorvector.append(noi)

        # #Descriptor2: loD density of low pitched instrumenst (kick and low conga)
        # #Descriptor3: midD density of the upbeat instruments(snare, rimshot, hiconga)
        # #Descriptor4: hiD density of high pitched sounds (closed hihat, shaker, clave)
        # #Descriptor5: stepD density: percentage of the steps that have onsets (loD+midD+hiD)
        # #descriptors 6 7 8: lowness, midness, hiness
    drumMidiMap = {}

    def __init__(self):
        self.descriptors = {
        "numberOfInstruments" : NumberOfTags(),
        "loD": Density(includedTags=["Kick","low Congas"]),
        "midD": Density(includedTags=["snare", "rimshot", "hiconga"]),
        "hiD": Density(includedTags=["closed hihat", "shaker", "clave"])}

    def getFeatureSpace(self, pattern):
        res = {}
        for d in self.descriptors:
            res[d] = self.descriptors[d].getDescriptorForPattern(pattern)
        return res

if __name__ == '__main__':
    from gsapi import *
    dataset = Dataset(midiGlob="*.mid")
    drumSpace = DensityDrumSpace()
    for p in dataset.patterns:
        print(drumSpace.getFeatureSpace(p))
