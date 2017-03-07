/*
  ==============================================================================

    Pattern.h
    Created: 8 Jun 2016 9:11:22am
    Author:  martin hermant

  ==============================================================================
*/

#ifndef PATTERN_H_INCLUDED
#define PATTERN_H_INCLUDED

#include "JSONSerializable.h"
#include "Event.h"

class Pattern: public JSONSerializable{

public:
	Pattern();
	virtual ~Pattern();
	
	string name;
	double originBPM;
	int timeSigNumerator,timeSigDenominator;
	double duration;

	vector<Event*> events;
	
	// for dynamicly adding event
	// void addEvent(const vector<string> & tags,Event && );
	void addEvent(Event * );

    void checkDurationValid();
    double getLastNoteOff();
    Event * getLastEvent();
  bool removeEvent(Event *);
	vector<Event*> getEventsWithTag(string tag);
	vector<Event*> getEventsWithPitch(int pitch);
	Pattern getCopyWithoutEvents();
private:

	 bool fillJSONData(json &) override;
	 bool getJSONData(const json &) override;
};

#endif  // PATTERN_H_INCLUDED
