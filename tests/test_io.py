#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from .test_utils import *


class GsioTest(GSTestBase):

    def generateCachedDataset(self):
        return gsdataset.Dataset(midiGlob="*.mid", midiFolder=self.getLocalCorpusPath('drums'),
                         midiMap="pitchName", checkForOverlapped=True)

    def test_ImportExportMidi(self):
        for p in self.cachedDataset:
            print(p.name)
            self.assertTrue(len(p.events)>0)
            exportedPath = gsio.toMidiFile(p, folderPath="../output/", name=p.name)
            exportedPath = os.path.abspath(exportedPath)
            self.assertTrue(os.path.exists(exportedPath))
            exportedP = gsio.fromMidiFile(exportedPath)
            # we have roundings error when converting to beats back and forth...
            self.checkPatternEquals(p, exportedP, tolerance=0.02)

    def test_ImportExportJSON(self):
        for p in self.cachedDataset:
            exportedPath = gsio.toJSONFile(p, folderPath="../output/", useTagIndexing=False, conserveTuple=False)
            jsonPattern = gsio.fromJSONFile(filePath=os.path.abspath(exportedPath), conserveTuple=False)
            self.checkPatternEquals(p, jsonPattern, checkViewpoints=False)

    def test_ImportExportJSONTuplesAndViewpoints(self):
        # chords descriptor return tuple so save it in json
        for p in self.cachedDataset:
            for name, descriptorClass in getAllDescriptorsClasses():
                p.generateViewpoint(name, descriptorClass(), sliceType=4)

            exportedPath = gsio.toJSONFile(p, folderPath="../output/", useTagIndexing=False, conserveTuple=True)
            self.assertTrue(os.path.exists(exportedPath))
            jsonPattern = gsio.fromJSONFile(filePath=os.path.abspath(exportedPath), conserveTuple=True)
            self.checkPatternEquals(p, jsonPattern, checkViewpoints=True)

    def test_ImportExportPickle(self):
        for p in self.cachedDataset:
            for name,descriptorClass in getAllDescriptorsClasses():
                p.generateViewpoint(name, descriptorClass(), sliceType=4)
            exportedPath = gsio.toPickleFile(p, folderPath="../output/")
            self.assertTrue(os.path.exists(exportedPath))
            picklePattern = gsio.fromPickleFile(filePath=os.path.abspath(exportedPath))
            self.checkPatternEquals(p, picklePattern, checkViewpoints=True)

if __name__ == '__main__':
    runTest(profile=False, getStat=False)
