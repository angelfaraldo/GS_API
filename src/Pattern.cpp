/*
 ==============================================================================

 Pattern.cpp
 Created: 8 Jun 2016 9:11:22am
 Author:  martin hermant

 ==============================================================================
 */

#include "Pattern.h"


Pattern::Pattern():duration(-1){};
Pattern::~Pattern(){};
// void Pattern::addEvent(const vector<string> & tags,Event && event){
// 	event.eventTags = allTags.getOrAddTagIds(tags);
// 	events.emplace_back(event);
// }


void Pattern::addEvent(Event * event){
    events.push_back(event);
}


bool Pattern::fillJSONData(json & j) {
    //	json  timeInfo = j["timeInfo"];
    //	originBPM = timeInfo["bpm"].get<double>();
    //	timeSigNumerator = timeInfo["timeSignature"][0];
    //	timeSigDenominator = timeInfo["timeSignature"][1];
    //	duration = timeInfo["duration"];
    //	allTags.initialize(j["eventTags"]);
    //
    //	for(auto & e:j["eventList"]){
    //		events.emplace_back(e["on"],e["duration"],e["pitch"],e["velocity"],e["tagsIdx"],&allTags);
    //	}
    return false;
};


void Pattern::checkDurationValid(){

    bool isValid = (duration>0) ;
    if(!isValid){
        double lastNoteOff = getLastNoteOff();
        isValid = duration> lastNoteOff && (duration - lastNoteOff < 20.0);

        if(!isValid){
            duration = lastNoteOff;
        }
    }
}


double Pattern::getLastNoteOff(){
    Event  *lastEv = getLastEvent();
    return (lastEv && lastEv->isValid())?lastEv->start+ lastEv->duration : 0;
}
vector<Event*> Pattern::getEventsWithTag(string tag){
	vector<Event*> res;
	for(auto & e:events){
		for(auto & t:e->eventTags){
			if(t==tag){
				res.push_back(e);
				break;
			}
		}
	}
	return res;
}

vector<Event*> Pattern::getEventsWithPitch(int pitch){
	vector<Event*> res;
	for(auto & e:events){
			if(e->pitch==pitch){
				res.push_back(e);¡
		}
	}
	return res;
}
Pattern Pattern::getCopyWithoutEvents(){
	Pattern p;
	p.name = name;
	p.duration = duration;
	p.timeSigDenominator = timeSigDenominator;
	p.timeSigNumerator = timeSigNumerator;
	p.originBPM = originBPM;
	return p;

}
Event * Pattern::getLastEvent(){
    return (events.size()>0) ? events[events.size()-1] : nullptr;
}
bool Pattern::removeEvent(Event * ev){
  auto it = find(events.begin(),events.end(),ev);
  bool found = it!=events.end();
  if(found){events.erase(it);}
  delete ev;
  return found;
}


bool Pattern::getJSONData(const json & j) {
    json  timeInfo = j["timeInfo"];
    originBPM = timeInfo["bpm"].get<double>();
    timeSigNumerator = timeInfo["timeSignature"][0];
    timeSigDenominator = timeInfo["timeSignature"][1];
    duration = timeInfo["duration"];
    // allTags.initialize(j["eventTags"]);

    for(auto & e:j["eventList"]){
        events.push_back(new Event(e["on"],e["duration"],e["pitch"],e["velocity"],e["tagsIdx"]));
    }

    return true;
};
