/*
 ==============================================================================

 PatternPlayer.h
 Created: 8 Jun 2016 6:48:48pm
 Author:  martin hermant

 ==============================================================================
 */

#ifndef PATTERNPLAYER_H_INCLUDED
#define PATTERNPLAYER_H_INCLUDED


#include "Pattern.h"
#include <map>

typedef struct MIDIMapEntry{
	MIDIMapEntry(int ch,int pi,int velocity):channel(ch),pitch(pi),velocity(velocity){}
	int channel;
	int pitch;
	int velocity;
	double endTime;
}MIDIMapEntry;

class PatternMidiMapper{
public:
	virtual ~PatternMidiMapper(){};

	virtual vector<MIDIMapEntry> getMIDINoteForEvent(const PatternEvent * e) =0;

};

class DummyMapper:public PatternMidiMapper{
public:
	int baseNote = 0;
	vector<MIDIMapEntry> getMIDINoteForEvent(const PatternEvent * e) override{
		vector<MIDIMapEntry> res;
//		for(auto & ev:e.eventTags){
			res.push_back(MIDIMapEntry(1,e->pitch+baseNote,e->velocity));
//		}
		return res;
	}

};

class LiveMapper:public PatternMidiMapper{
public:
	std::map<string,int> tagToLiveMidi = {
		{"Kick",36},
		{"Snare",40},
		{"ClosedHH",42},
		{"OpenHH",46},
		{"Clap",39},
		{"Rimshot",37},
		{"LowConga",43},
		{"HiConga",47}};
	vector<MIDIMapEntry> getMIDINoteForEvent(const PatternEvent * e) override{
		vector<MIDIMapEntry> res;
		vector<string> tags = e->getTagNames();
		for(auto & t:tags){
			auto it = tagToLiveMidi.find(t);
			if(it!=tagToLiveMidi.end())
				res.push_back(MIDIMapEntry(1,it->second,e->velocity));
		}
		return res;
	}
};

class PatternPlayer{
public:

	typedef struct{
		vector<MIDIMapEntry> entries;
		double duration;
		double startTime;
	}MIDINoteEntries;

	PatternPlayer(PatternMidiMapper * mmap):isLooping(true),ownedMapper(mmap){}


	void updatePlayHead(double pH);
	vector<MIDIMapEntry> &getCurrentNoteOn();
	vector<MIDIMapEntry> &getCurrentNoteOff();


	Pattern  currentPattern;

	void setMidiMapper(PatternMidiMapper * mmap);
	void setPattern(const Pattern &);
	void stop();
	bool isLooping;
private:

	double playHead,lastPlayHead;
	PatternMidiMapper * ownedMapper;

	vector<MIDIMapEntry> currentNote;
	vector<MIDIMapEntry> currentNoteOn;
	vector<MIDIMapEntry> currentNoteOff;
};

#endif  // PATTERNPLAYER_H_INCLUDED
