/*
  ==============================================================================

    Style.h
    Created: 8 Jun 2016 9:11:32am
    Author:  martin hermant

  ==============================================================================
*/

#ifndef STYLE_H_INCLUDED
#define STYLE_H_INCLUDED

#include "JSONSerializable.h"

class Style:public JSONSerializable{
public:
	Style();
	virtual ~Style();
	virtual bool fillJSONData(json &) override;
	virtual bool getJSONData(const json &) override;
};

#endif  // STYLE_H_INCLUDED
