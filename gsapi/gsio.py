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

if sys.version_info >= (3, 0):
    import pickle
else:
    import cPickle as pickle

from . import gsdefs, gspattern, gsutil, midiio


gsioLog = logging.getLogger("gsapi.gsio")
gsioLog.setLevel(level=logging.WARNING)


def __keyToMidiFormat(keyString):
    mode = 0
    if 'm' in keyString:
        keyString = keyString[:-1]
        mode = 1
    tonic = gsdefs.midiKey.keys()[gsdefs.midiKey.values().index(keyString)]
    return tonic, mode


def __metaEventsFromMidiFile(myPattern, midiFile):
    foundTimeSignatureEvent = False
    foundTempo = False
    foundKey = False
    myPattern.timeSignature = (4, 4)
    myPattern.bpm = 120
    myPattern.key = ""
    myPattern.resolution = midiFile.resolution

    for tracks in midiFile:
        for e in tracks:
            if midiio.MetaEvent.is_event(e.statusmsg):
                if e.metacommand == midiio.TimeSignatureEvent.metacommand:
                    if foundTimeSignatureEvent and (myPattern.timeSignature != (e.numerator, e.denominator)):
                        gsioLog.error(myPattern.name + ": found multiple time signatures! Not supported.")
                    foundTimeSignatureEvent = True
                    myPattern.timeSignature = (e.numerator, e.denominator)
                elif e.metacommand == midiio.SetTempoEvent.metacommand:
                    if foundTempo:
                        gsioLog.error(myPattern.name + ": found multiple tempi! Not supported.")
                    foundTempo = True
                    myPattern.bpm = e.bpm
                elif e.metacommand == midiio.KeySignatureEvent.metacommand:
                    if foundKey:
                        gsioLog.error(myPattern.name + ": found multiple keys! Not supported.")
                    foundKey = True
                    keyName = gsdefs.midiKey[e.alternatives]
                    if e.minor == 1:
                        keyName += "m"
                    myPattern.key = keyName

                    # if foundTimeSignatureEvent:
                    #    break
    if not foundTimeSignatureEvent:
        gsioLog.info(myPattern.name + ": no Time Signature event found.")
    if not foundTempo:
        gsioLog.info(myPattern.name + ": no Tempo event found.")
    if not foundKey:
        gsioLog.info(myPattern.name + ": no Key event found.")


def __tagFromMidiNote(_noteToTag):
    noteToTag = copy.copy(_noteToTag)
    if noteToTag == "pitchName":
        noteToTag = {"pitchName": ""}
    for n in noteToTag:
        if n == "pitchName":
            if not noteToTag["pitchName"]:
                noteToTag["pitchName"] = gsdefs.defaultPitchNames
        else:
            if not isinstance(noteToTag[n], list):
                noteToTag[n] = [noteToTag[n]]
            for i in range(len(noteToTag[n])):
                if isinstance(noteToTag[n][i], int):
                    noteToTag[n][i] = (noteToTag[n][i], "*")
    return noteToTag


def __tagsFromMidiNoteAndChannel(pitch, channel, noteMapping):
    if "pitchName" in noteMapping.keys():
        return gsutil.pitch2name(pitch, noteMapping["pitchName"])

    res = tuple()
    for l in noteMapping:
        for le in noteMapping[l]:
            if (le[0] in {"*", pitch}) and (le[1] in {"*", channel}):
                res += (l,)
    if len(res) == 1:
        return res[0]
    return res


def __tagFromTrackName(name, noteMapping):
    res = tuple()
    for l in noteMapping:
        if l in name:
            res += [l]
    return res


def __fromMidiFormat(midiPath, noteToTagMap, tracksToGet=None, tagFromTrackName=False,
                     filterOutNotMapped=True, checkForOverlapped=False):
    """
    Internal function that accepts only consistent noteTagMap
    structures as created by __tagFromMidiNote.

    """
    globalMidi = midiio.read_midifile(midiPath)
    globalMidi.make_ticks_abs()
    myPattern = gspattern.Pattern()
    myPattern.name = os.path.basename(midiPath)

    # boolean to avoid useless string creation
    extremeLog = gsioLog.getEffectiveLevel() <= logging.DEBUG

    # Get time signature first
    gsioLog.info("start processing %s" % myPattern.name)
    __metaEventsFromMidiFile(myPattern, globalMidi)

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
            if not tagFromTrackName:
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
                        gsioLog.info(myPattern.name + ": getting track: %i %s" % (trackIdx, e.text))

                    if tagFromTrackName:
                        noteTag = __tagFromTrackName(e.text, noteToTagMap)

            if midiio.EndOfTrackEvent.is_event(e.statusmsg):
                thisDuration = e.tick * tick_to_quarter_note
                trackDuration = max(trackDuration, thisDuration) if trackDuration else thisDuration
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
                    if tagFromTrackName:
                        continue
                    noteTag = __tagsFromMidiNoteAndChannel(pitch, e.channel, noteToTagMap)

                if not noteTag:
                    if [e.channel, pitch] not in notFoundTags:
                        gsioLog.info(myPattern.name +
                                     ": no tags found for pitch %d on channel %d"
                                     % (pitch, e.channel))
                        notFoundTags += [[e.channel, pitch]]
                    if filterOutNotMapped:
                        continue
                if isNoteOn:
                    if extremeLog: gsioLog.debug("on %d %f" % (pitch, curBeat))
                    myPattern.events += [gspattern.Event(startTime=curBeat, duration=-1, pitch=pitch,
                                                         velocity=velocity, tag=noteTag)]
                if isNoteOff:
                    if extremeLog:
                        gsioLog.debug("off %d %f" % (pitch, curBeat))
                    foundNoteOn = False
                    isTrueNoteOff = midiio.NoteOffEvent.is_event(e.statusmsg)
                    for i in reversed(myPattern.events):
                        if (i.pitch == pitch) and (i.tag == noteTag) and ((isTrueNoteOff and (curBeat >= i.startTime))
                                                                    or curBeat > i.startTime) and i.duration <= 0.0001:
                            foundNoteOn = True
                            i.duration = max(0.0001, curBeat - i.startTime)
                            lastNoteOff = max(curBeat, lastNoteOff)
                            gsioLog.info("set duration %f at start %f " % (i.duration, i.startTime))
                            break
                    if not foundNoteOn:
                        gsioLog.warning(myPattern.name + ": not found note on\n %s\n%s\n%s , %s " %
                                        (e, myPattern.events[-1], noteTag, curBeat))
        trackIdx += 1
    elementSize = 4.0 / myPattern.timeSignature[1]
    barSize = myPattern.timeSignature[0] * elementSize
    lastBarPos = math.ceil(lastNoteOff * 1.0 / barSize) * barSize
    myPattern.duration = trackDuration or lastBarPos
    if checkForOverlapped:
        myPattern.removeOverlapped(usePitchValues=True)
    return myPattern


def fromMidiFile(midiFile, noteToTagMap="pitchName", tracksToGet=None, tagFromTrackName=False,
                 filterOutNotMapped=True, checkForOverlapped=False):
    # TODO: tagFromTrackName=True returns an eventless pattern!
    """
    Loads a MIDI file as a pattern.

    Parameters
    ----------
    midiFile: str
        a valid midi filePath.
    noteToTagMap: dict
        a dictionary converting pitches to tags.
    tracksToGet: list of str or int
        if not empty, specifies Midi tracks wanted either by name or index
    tagFromTrackName: bool
        use only track names to resolve mapping.
        Useful for midi containing named tracks.
    filterOutNotMapped: bool
        if True, don't add event not represented by `NoteToTagsMap`.
    checkForOverlapped: bool
        If True, will check that two consecutive Events with exactly same
        Midi Note are not overlapping.

    Notes
    -----
    You can set NoteToTagsMap to "pitchName" or optionally set the value to
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
    _noteToTagMap = __tagFromMidiNote(noteToTagMap)
    return __fromMidiFormat(midiPath=midiFile, noteToTagMap=_noteToTagMap, tracksToGet=tracksToGet,
                            tagFromTrackName=tagFromTrackName, filterOutNotMapped=filterOutNotMapped,
                            checkForOverlapped=checkForOverlapped)


def fromMidiCollection(midiGlobPath, noteToTagMap=gsdefs.defaultPitchNames, tracksToGet=None,
                       tagFromTrackName=False, filterOutNotMapped=True, desiredLength=0):
    """
    Loads a collection of MIDI Files

    Parameters
    ----------
    midiGlobPath: str
        midi filePath in glob style naming convention ('/midi/folder/*.mid')
    noteToTagMap: dict
        a dictionary converting pitches to tags.
    tracksToGet: str or int
        if not empty, specifies Midi tracks wanted either by name or index
    tagFromTrackName: bool
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
    _noteToTagMap = __tagFromMidiNote(noteToTagMap)
    for f in glob.glob(midiGlobPath):
        name = os.path.splitext(os.path.basename(f))[0]
        gsioLog.info("getting " + name)
        p = fromMidiFile(f, _noteToTagMap, tagFromTrackName=tagFromTrackName, filterOutNotMapped=filterOutNotMapped)
        if desiredLength > 0:
            res += p.splitInEqualLengthPatterns(desiredLength, makeCopy=False)
        else:
            res += [p]
    return res


def toMidiFile(myPattern, midiMap=gsdefs.defaultPitchNames, folderPath="./output/", name=None):
    """
    Function to write a Pattern to a MIDI file.

    Parameters
    ----------
    myPattern: Pattern
        A reference to a Pattern
    midiMap: dict
        mapping used to translate tags to MIDI pitch.
        see "gsdefs.py" for implemented midiMaps
    folderPath: str
        a valid folderpath where the MIDI file will be stored.
    name: str
        name of the file to write to.
    """

    # Instantiate a MIDI myPattern (contains a list of tracks)
    pattern = midiio.Pattern(tick_relative=False, frmt=1)
    pattern.resolution = getattr(myPattern, 'resolution', 960)

    # Instantiate a MIDI track (contains a list of MIDI events)
    track = midiio.Track(tick_relative=False)

    # Write Metadata
    track.append(midiio.TimeSignatureEvent(numerator=myPattern.timeSignature[0],
                                           denominator=myPattern.timeSignature[1]))
    track.append(midiio.TrackNameEvent(text=myPattern.name))
    track.append(midiio.SetTempoEvent(bpm=myPattern.bpm))
    if myPattern.key:
        keyTuple = __keyToMidiFormat(myPattern.key)
        track.append(midiio.KeySignatureEvent(alternatives=keyTuple[0], minor=keyTuple[1]))

    # Append the track to the pattern
    pattern.append(track)
    beatToTick = pattern.resolution
    for e in myPattern.events:
        startTick = int(beatToTick * e.startTime)
        endTick = int(beatToTick * e.endTime())
        # pitch = e.pitch
        channel = 1
        if isinstance(midiMap, tuple):
            pitch = midiMap[e.tag[0]]
        elif isinstance(midiMap, collections.Hashable):
            pitch = midiMap[e.tag]
        else:
            pitch = e.pitch
        track.append(midiio.NoteOnEvent(tick=startTick, velocity=e.velocity, pitch=pitch, channel=channel))
        track.append(midiio.NoteOffEvent(tick=endTick, velocity=e.velocity, pitch=pitch, channel=channel))

    # and the "End of Track" Event
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


def toJSONFile(myPattern, folderPath, useTagIndexing=True, nameSuffix=None, conserveTuple=False):
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
