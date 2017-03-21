#!/usr/bin/env python
# encoding: utf-8
"""
The gsio module contains fuctions allowing importing and exporting to and from
various standards formats (MIDI, JSON and Python's pickle).
"""

from __future__ import absolute_import, division, print_function

import copy
import collections
import glob
import json
import logging
import math
import os
import sys



from . import gsdefs, gspattern, gsutil, midiio

if sys.version_info >= (3, 0):
    import pickle
else:
    import cPickle as pickle

gsioLog = logging.getLogger("gsapi.gsio")
gsioLog.setLevel(level=logging.WARNING)


# PRIVATE FUNCTIONS
# =============================================================================

def __formatNoteToTags(_noteToTags):
    """
    Private conversion for consistent noteTagMap structure.

    """
    noteToTags = copy.copy(_noteToTags)
    if noteToTags == "pitchNames":
        noteToTags = {"pitchNames": ""}
    for n in noteToTags:
        if n == "pitchNames":
            if not noteToTags["pitchNames"]:
                noteToTags["pitchNames"] = gsdefs.pitchNames
        else:
            if not isinstance(noteToTags[n], list):
                noteToTags[n] = [noteToTags[n]]
            for i in range(len(noteToTags[n])):
                if isinstance(noteToTags[n][i], int):
                    noteToTags[n][i] = (noteToTags[n][i], "*")
    return noteToTags


def __findTimeInfoFromMidi(myPattern, midiFile):
    foundTimeSignatureEvent = False
    foundTempo = False
    myPattern.timeSignature = (4, 4)
    myPattern.bpm = 120
    # hide it in myPattern to be able to retrieve it when exporting
    myPattern.resolution = midiFile.resolution

    for tracks in midiFile:
        for e in tracks:
            if midiio.MetaEvent.is_event(e.statusmsg):
                if e.metacommand == midiio.TimeSignatureEvent.metacommand:
                    if foundTimeSignatureEvent and (
                                myPattern.timeSignature != (
                                    e.numerator, e.denominator)):
                        gsioLog.error(myPattern.name + ": multiple time "
                                                       "signature found, not supported, "
                                                       "result can be altered")
                    foundTimeSignatureEvent = True
                    myPattern.timeSignature = (e.numerator, e.denominator)
                elif e.metacommand == midiio.SetTempoEvent.metacommand:
                    if foundTempo:
                        gsioLog.error(myPattern.name + ": multiple bpm found, not supported")
                    foundTempo = True
                    myPattern.bpm = e.bpm

        if foundTimeSignatureEvent:
            break
    if not foundTimeSignatureEvent:
        gsioLog.info(myPattern.name + ": no timeSignature event found")


# def __findTagsFromName(name, noteMapping):
#     res = tuple()
#     for l in noteMapping:
#         if l in name:
#             res += [l]
#     return res


# def __findTagsFromPitchAndChannel(pitch, channel, noteMapping):
#     if "pitchNames" in noteMapping.keys():
#         return gsutil.pitch2name(pitch, noteMapping["pitchNames"])
#
#     res = tuple()
#     for l in noteMapping:
#         for le in noteMapping[l]:
#             if (le[0] in {"*", pitch}) and (le[1] in {"*", channel}):
#                 res += (l,)
#     if len(res) == 1:
#         return res[0]
#     return res


def __fromMidiFormatted(midiPath, noteToTagsMap, tracksToGet=None,
                        tagsFromTrackNameEvents=False, filterOutNotMapped=True,
                        checkForOverlapped=False):
    """
    Internal function that accepts only consistent noteTagMap
    structures as created by __formatNoteToTags.

    """
    globalMidi = midiio.read_midifile(midiPath)
    globalMidi.make_ticks_abs()
    myPattern = gspattern.Pattern()
    myPattern.name = os.path.basename(midiPath)

    # boolean to avoid useless string creation
    extremeLog = gsioLog.getEffectiveLevel() <= logging.DEBUG

    # get time signature first
    gsioLog.info("start processing %s" % myPattern.name)
    __findTimeInfoFromMidi(myPattern, globalMidi)

    tick_to_quarter_note = 1.0 / globalMidi.resolution
    myPattern.events = []
    lastNoteOff = 0
    notFoundTags = []
    trackIdx = 0
    trackDuration = None
    for tracks in globalMidi:
        shouldSkipTrack = False
        for e in tracks:
            if shouldSkipTrack:
                continue
            if not tagsFromTrackNameEvents:
                noteTag = ()
            if midiio.MetaEvent.is_event(e.statusmsg):
                if e.metacommand == midiio.TrackNameEvent.metacommand:
                    if tracksToGet and not (
                        (e.text in tracksToGet) or (trackIdx in tracksToGet)):
                        gsioLog.info(
                            "skipping track: %i %s" % (trackIdx, e.text))
                        shouldSkipTrack = True
                        continue
                    else:
                        gsioLog.info(
                            myPattern.name + ": getting track: %i %s" % (
                            trackIdx, e.text))

                    if tagsFromTrackNameEvents:
                        #noteTag = __findTagsFromName(e.text, noteToTagsMap)
                        noteTag = tuple()
                        for l in noteToTagsMap:
                            if l in e.text:
                                noteTag += [l]

            if midiio.EndOfTrackEvent.is_event(e.statusmsg):
                thisDuration = e.tick * tick_to_quarter_note
                trackDuration = max(trackDuration,
                                    thisDuration) if trackDuration else thisDuration
                continue
            isNoteOn = midiio.NoteOnEvent.is_event(e.statusmsg)
            isNoteOff = midiio.NoteOffEvent.is_event(e.statusmsg)
            if isNoteOn or isNoteOff:
                pitch = e.pitch  # optimize pitch property access
                tick = e.tick
                velocity = e.get_velocity()
                if velocity == 0:
                    isNoteOff = True
                    isNoteOn = False
                curBeat = tick * 1.0 * tick_to_quarter_note
                if not noteTag:
                    if tagsFromTrackNameEvents:
                        continue
#                   # noteTag = __findTagsFromPitchAndChannel(pitch, e.channel, noteToTagsMap)
                    if "pitchNames" in noteToTagsMap.keys(): # TODO ESTA LINEA
                        noteTag = gsutil.pitch2name(pitch, noteToTagsMap["pitchNames"])
                    else:
                        noteTag = tuple()
                        for l in noteToTagsMap:
                            for le in noteToTagsMap[l]:
                                if (le[0] in {"*", pitch}) and (le[1] in {"*", e.channel}):
                                    noteTag += (l,)
                        if len(noteTag) == 1:
                            noteTag = noteTag[0]
                if not noteTag:
                    if [e.channel, pitch] not in notFoundTags:
                        gsioLog.info(myPattern.name + ": no tags found for "
                                                      "pitch %d on channel %d" % (
                                     pitch, e.channel))
                        notFoundTags += [[e.channel, pitch]]
                    if filterOutNotMapped:
                        continue
                if isNoteOn:
                    if extremeLog: gsioLog.debug("on %d %f" % (pitch, curBeat))
                    myPattern.events += [gspattern.Event(startTime=curBeat,
                                                         duration=-1,
                                                         pitch=pitch,
                                                         velocity=velocity,
                                                         tag=noteTag)]
                if isNoteOff:
                    if extremeLog:
                        gsioLog.debug("off %d %f" % (pitch, curBeat))
                    foundNoteOn = False
                    isTrueNoteOff = midiio.NoteOffEvent.is_event(e.statusmsg)
                    for i in reversed(myPattern.events):
                        if (i.pitch == pitch) and (i.tag == noteTag) and \
                                ((isTrueNoteOff and (
                                    curBeat >= i.startTime)) or curBeat > i.startTime) \
                                and i.duration <= 0.0001:
                            foundNoteOn = True
                            i.duration = max(0.0001, curBeat - i.startTime)
                            lastNoteOff = max(curBeat, lastNoteOff)
                            gsioLog.info("set duration %f at start %f " % (
                            i.duration, i.startTime))
                            break
                    if not foundNoteOn:
                        gsioLog.warning(myPattern.name +
                                        ": not found note on\n %s\n%s\n%s , %s "
                                        % (e, myPattern.events[-1], noteTag,
                                           curBeat))
        trackIdx += 1
    elementSize = 4.0 / myPattern.timeSignature[1]
    barSize = myPattern.timeSignature[0] * elementSize
    lastBarPos = math.ceil(lastNoteOff * 1.0 / barSize) * barSize
    myPattern.duration = trackDuration or lastBarPos
    if checkForOverlapped:
        myPattern.removeOverlapped(usePitchValues=True)
    return myPattern


# MIDI
# =============================================================================

def fromMidi(midiFile, noteToTagsMap=gsdefs.pitchNames, tracksToGet=None,
             tagsFromTrackNameEvents=False, filterOutNotMapped=True,
             checkForOverlapped=False):
    """
    Loads a MIDI file as a pattern.

    Parameters
    ----------
    midiFile: str
        a valid midi filePath.
    noteToTagsMap: dict
        a dictionary converting pitches to tags.
    tracksToGet: list of str or int
        if not empty, specifies Midi tracks wanted either by name or index
    tagsFromTrackNameEvents: bool
        use only track names to resolve mapping.
        Useful for midi containing named tracks.
    filterOutNotMapped: bool
        if True, don't add event not represented by `NoteToTagsMap`.
    checkForOverlapped: bool
        If True, will check that two consecutive Events with exactly same
        Midi Note are not overlapping.

    Notes
    -----
    You can set NoteToTagsMap to "pitchNames" or optionally set the value to
    the list of string for pitches from C. noteMapping maps classes to a list
    of possible mappings. A mapping can be either:

    * a tuple of (note, channel):
        if one of those does not matter it can be replaced by a '*' character
    * an integer:
        if only pitch matters

    For simplicity, one can pass only one integer (i.e not a list) for
    one to one mappings. If the MIDI track contains the name of one element
    of the mapping, it'll be choosen without anyother consideration

    """
    _noteToTagsMap = __formatNoteToTags(noteToTagsMap)
    return __fromMidiFormatted(midiPath=midiFile,
                               noteToTagsMap=_noteToTagsMap,
                               tracksToGet=tracksToGet,
                               tagsFromTrackNameEvents=tagsFromTrackNameEvents,
                               filterOutNotMapped=filterOutNotMapped,
                               checkForOverlapped=checkForOverlapped)


def fromMidiCollection(midiGlobPath, noteToTagsMap=gsdefs.pitchNames,
                       tracksToGet=None, tagsFromTrackNameEvents=False,
                       filterOutNotMapped=True, desiredLength=0):
    """
    Loads a collection of MIDI Files

    Parameters
    ----------
    midiGlobPath: str
        midi filePath in glob style naming convention ('/midi/folder/*.mid')
    noteToTagsMap: dict
        a dictionary converting pitches to tags.
    tracksToGet: str or int
        if not empty, specifies Midi tracks wanted either by name or index
    tagsFromTrackNameEvents: bool
        use only track names to resolve mapping.
        Useful for midi containing named tracks.
    filterOutNotMapped: bool
        if True, don't add event not represented by `NoteToTagsMap`.
    desiredLength: float
        optionally cut patterns in equal length

    Returns
    -------
    A list of patterns build from the Midi folder

    """
    res = []
    _noteToTagsMap = __formatNoteToTags(noteToTagsMap)
    for f in glob.glob(midiGlobPath):
        name = os.path.splitext(os.path.basename(f))[0]
        gsioLog.info("getting " + name)
        p = fromMidi(f, _noteToTagsMap,
                     tagsFromTrackNameEvents=tagsFromTrackNameEvents,
                     filterOutNotMapped=filterOutNotMapped)
        if desiredLength > 0:
            res += p.splitInEqualLengthPatterns(desiredLength, makeCopy=False)
        else:
            res += [p]
    return res


def toMidi(myPattern, midiMap=gsdefs.noteMap, folderPath="./", name=None):
    """
    Function to write a Pattern to a MIDI file.

    Parameters
    ----------
    myPattern: str
        A reference to a Pattern
    midiMap: dict
        mapping used to translate tags to MIDI pitch.
        see "gsdefs.py" for implemented midiMaps
    folderPath: str
        a valid folderpath where the MIDI file will be stored.
    name: str
        name of the file to write to.
    """

    # Instantiate a MIDI Pattern (contains a list of tracks)
    pattern = midiio.Pattern(tick_relative=False, frmt=1)
    pattern.resolution = getattr(myPattern, 'resolution', 960)

    # Instantiate a MIDI track (contains a list of MIDI events)
    track = midiio.Track(tick_relative=False)

    track.append(midiio.TimeSignatureEvent(numerator=myPattern.timeSignature[0],
                                         denominator=myPattern.timeSignature[1]))
    track.append(midiio.TrackNameEvent(text=myPattern.name))
    track.append(midiio.SetTempoEvent(bpm=myPattern.bpm))

    # Append the track to the pattern
    pattern.append(track)
    beatToTick = pattern.resolution
    for evt in myPattern.events:
        startTick = int(beatToTick * evt.startTime)
        endTick = int(beatToTick * evt.getEndTime())
        # pitch = e.pitch
        channel = 1
        if isinstance(midiMap, tuple):
            pitch = midiMap[evt.tag[0]] # provided a key return pitch value
        elif isinstance(midiMap, collections.Hashable):
            pitch = midiMap[evt.tag]
        #elif midiMap is None: # todo: confirm that this condition sobra!
         #   pitch = evt.pitch
        else:
            pitch = evt.pitch  # todo esto lo he movido de más arriba!
        track.append(midiio.NoteOnEvent(tick=startTick, velocity=evt.velocity,
                                          pitch=pitch, channel=channel))
        track.append(midiio.NoteOffEvent(tick=endTick, velocity=evt.velocity,
                                           pitch=pitch, channel=channel))

    track.append(midiio.EndOfTrackEvent(tick=int(myPattern.duration * beatToTick)))

    # make tick relatives
    track.sort(key=lambda e: e.tick)
    track.make_ticks_rel()

    # Save the pattern to disk
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    name = name or myPattern.name
    name = name or "tests"
    if ".mid" not in name:
        name += ".mid"
    exportedPath = os.path.join(folderPath, name)

    midiio.write_midifile(exportedPath, pattern)
    return exportedPath


# JSON
# =============================================================================

def fromJSONFile(filePath, conserveTuple=False):
    """
    Loads a pattern to the internal JSON Format.

    Parameters
    ----------
    filePath: path
        filePath where to load it
    conserveTuple: bool
        Useful if some tags were tuples, but performs more slowly.

    """
    def hinted_tuple_hook(obj):
        if isinstance(obj, list): return [hinted_tuple_hook(e) for e in obj]
        if isinstance(obj, dict):
            if '__tuple__' in obj: return tuple(obj['items'])
            return {k: hinted_tuple_hook(e) for k, e in obj.items()}
        else:
            return obj

    with open(filePath, 'r') as f:
        return gspattern.Pattern().fromJSONDict(json.load(f, object_hook=hinted_tuple_hook if conserveTuple else None))


def toJSONFile(myPattern, folderPath, useTagIndexing=True,
               nameSuffix=None, conserveTuple=False):
    """
    Saves a pattern to internal JSON Format.

    Parameters
    ----------
    myPattern: Pattern
        the Pattern to save.
    folderPath: path
        folder to save the file.
        the fileName will be pattern.name+nameSuffix+".json"
    nameSuffix: str
        string to append to name of the file
    useTagIndexing: bool
        if True, tags are stored as indexes from a list of all tags.
        this reduces the size of JSON files.
    conserveTuple: bool
        useful if some tags were tuples, but performs more slowly.
    """

    filePath = os.path.join(folderPath, myPattern.name + (nameSuffix or "") + ".json")
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    class TupleEncoder(json.JSONEncoder):
        """
        Encoder conserving tuple type information.

        """
        def checkTuple(self, item):
            if isinstance(item, tuple): return {'__tuple__': True, 'items': item}
            if isinstance(item, list): return [self.checkTuple(e) for e in item]
            if isinstance(item, dict):
                return {k: self.checkTuple(e) for k, e in item.items()}
            else:
                return item

        def iterencode(self, item):
            return json.JSONEncoder.iterencode(self, self.checkTuple(item))

    encoderClass = TupleEncoder if conserveTuple else None
    with open(filePath, 'w') as f:
        json.dump(myPattern.toJSONDict(useTagIndexing=useTagIndexing), f,
                  cls=encoderClass, indent=1, separators=(',', ':'))
    return os.path.abspath(filePath)


# PICKLE
# =============================================================================

def fromPickleFile(filePath):
    """
    Loads a pattern from a pickle format.

    Parameters
    ----------
    filePath: path
        file path where to load it.

    """
    with open(filePath, 'rb') as f:
        return pickle.load(f)


def toPickleFile(myPattern, folderPath, nameSuffix=None):
    """
    Saves a pattern into python's pickle format.

    Parameters
    ----------
    myPattern: Pattern
        the Pattern to save.
    folderPath: path
        the folder where to save the pickle file.
        The fileName will be pattern.name + nameSuffix + ".pickle"
    nameSuffix: str
        string to append to the name of the file.

    """
    filePath = os.path.join(folderPath, myPattern.name + (nameSuffix or "") + ".pickle")
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    with open(filePath, 'wb') as f:
        pickle.dump(myPattern, f)
    return os.path.abspath(filePath)


def write2pickle(name, data, path='../models/'):
    """
    Write numpy array in pickle format to the selected location.

    Arguments
    ---------
    name: str
        name of the output pickle file
    data: numpy array
        numpy array to be exported to pickle format
    path: str (optional)
         output folder path

    """
    if not os.path.exists(path):
        os.makedirs(path)
    with open(path + name + '.pickle', 'wb') as f:
        # Pickle the 'data' dictionary using the highest protocol available.
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
