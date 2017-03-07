/*
  ==============================================================================

    Event.h
    Created: 8 Jun 2016 4:46:34pm
    Author:  martin hermant

  ==============================================================================
*/

#ifndef EVENT_H_INCLUDED
#define EVENT_H_INCLUDED

#include <vector>
#include <string>
using namespace std;

class Event{
public:
    Event():duration(0){}
	Event(const double _start,
				   const double _duration,
				   const int _pitch,
				   const int _velocity,
				   const vector<string> & tags
				   )
	:
	start(_start),
	duration(_duration),
	pitch(_pitch),
	velocity(_velocity),
	eventTags(tags)
	{}

	double start;
	double duration;
	int pitch;
	int velocity;
	vector<string> eventTags;

    bool isValid();

	double getEndTime(){return start+duration;}

    static Event empty;
	
	 vector<string> getTagNames() const;
	
};

#endif  // EVENT_H_INCLUDED
