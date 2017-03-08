Example using JUCE library
==========================
this VST Plugin is for testing purpose only.

this VST loads a python file (python/VSTPlugin.py) 
and implements a basic API to:

* display and play a Pattern
* call python functions from the VST User Interface


### Interface

A basic interface allows to show the python file being processed, 
reloading it and autowatching the file (reload each time the file is modified).
The file is in the VST bundle, under "Resources/python"

You need to install python-gsapi first. See GSAPI Readme file.


### Dependencies

Cython, numpy, python-midi

### Known Bugs
-
By now it works in pretty much all DAWs 
(Bitwig, JUCEAudiopluginHostDemo, Reaper),
 except it does not work in Ableton Live.
