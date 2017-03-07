/*
  ==============================================================================

    Event.cpp
    Created: 8 Jun 2016 5:04:28pm
    Author:  martin hermant

  ==============================================================================
*/

#include "Event.h"

Event Event::empty;

vector<string>  Event::getTagNames() const{
	return eventTags;	
}

bool Event::isValid(){
    return duration>0;
}
