# inject develop version of gsapi if debugging
if __name__=='__main__':
	import sys,os
	pathToAdd = os.path.abspath(os.path.join(__file__,os.path.pardir,os.path.pardir,os.path.pardir,os.path.pardir,"python"))
	sys.path.insert(1,pathToAdd)
	print sys.path

from gsapi import *
from gsapi.GSInternalStyles import *
import json
import glob
import random
import os
from UIParameter import UIParameter


""" this example generates random notes to demonstrate passing GSPattern to C++ plugin
"""
midiMap = {
		"Kick":36,
		"Rimshot":37,
		"Snare":38,
		"Clap":39,
		"Clave":40,
		"LowTom":41,
		"ClosedHH":42,
		"MidTom":43,
		"Shake":44,
		"HiTom":45,
		"OpenHH":46,
		"LowConga":47,
		"HiConga":48,
		"Cymbal":49,
		"Conga":50,
		"CowBell":51
}

localDirectory = os.path.abspath(os.path.join(__file__,os.path.pardir))

searchPath = os.path.join(localDirectory,"midi","garagehouse1_snare.mid");
# searchPath = os.path.join(localDirectory,"midi","daftpunk2.mid");
# searchPath = os.path.join(localDirectory,"midi","motown.mid");
# searchPath = os.path.join(localDirectory,"midi","nj-house.mid");

styleSavingPath = os.path.join(localDirectory,"DBStyle.json");

style = GSMarkovStyle(order=2,numSteps=32,loopDuration=4)
# style = GSDBStyle(generatePatternOrdering = "increasing");
needStyleUpdate = True;

def setup():
	print "settingThingsUp"
	

def onTimeChanged(time):
	""" called at eacch beat when pattern is playing
	Args:
		a dictionary {'time':timeinBeat}
	Returns:
 		the new GSpattern to be played if needed
	"""
	
	return None

def updateTest():
	print "pyrcv"

def getAllParameters():
	""" should return a list of params to be displayed in VST GUI
	"""
	res = []
	test = UIParameter(10,0,0,50,100)
	test.onChange = updateTest
	test.value = 10
	res+=[test]
	return res;



def onGenerateNew():
	""" called when user press generate new
	Returns:
	 the new GSpattern to be played
	"""
	global style
	generateStyleIfNeeded();
	print "start generating pattern"
	pattern = style.generatePattern();
	print "mapMidi"
	mapMidi(pattern)


	print "ended"
	return pattern

def mapMidi(pattern):
	for e in pattern.events:
		if len(e.tags) > 0 and (e.tags[0] in midiMap):
			e.pitch = midiMap[e.tags[0]]


def generateStyleIfNeeded():
	global needStyleUpdate
	global midiMap
	global style

	if not style.isBuilt():
		hasStyleSaved = os.path.isfile(styleSavingPath)
		if(not hasStyleSaved  or needStyleUpdate ):
			print "startGenerating for "+searchPath+" : "+str(glob.glob(searchPath))
			patterns = gsapi.GSIO.fromMidiCollection(searchPath,NoteToTagsMap=midiMap,TagsFromTrackNameEvents=False,desiredLength = 4)
			style.generateStyle(patterns)
			style.saveToJSON(styleSavingPath)
			needStyleUpdate =False
		else:
			style.loadFromJSON(styleSavingPath)
	


def transformPattern(patt):
	i = 0;
	j=1
	for e in patt.events:
		e.startTime+=(random.random()*2.0 - 1)*.4
		e.duration=max(0.1,e.duration+(random.random()*2.0-1)*.4)
	return patt


if __name__ =='__main__':
	print "runMain"
	needStyleUpdate=True
	patt = onGenerateNew();
	params =  getAllParameters()
	print dir(params[0])
	for property, value in vars(params[0]).iteritems():
		print property, ": ", value
	
	# patt.printEvents()