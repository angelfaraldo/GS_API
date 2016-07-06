/*
 ==============================================================================
 
 PyJUCEAPI.h
 Created: 13 Jun 2016 5:00:10pm
 Author:  Martin Hermant
 
 ==============================================================================
 */

#ifndef PYJUCEAPI_H_INCLUDED
#define PYJUCEAPI_H_INCLUDED

#include "JuceHeader.h"

#include "GS_API.h"
#include "GSPatternPyWrap.h"

#include "pythonWrap.h"
#include "TimeListener.h"

#include "PyJUCEParameter.h"

class PyJUCEAPI : public Timer,public TimeListener{
public:
  PyJUCEAPI():TimeListener(1){timePyObj = PyDict_New();timeKey=PyFromString("time");}
	~PyJUCEAPI(){Py_DECREF(timePyObj);Py_DECREF(timeKey);}
	
  void load();
  void init();
  bool isLoaded();
  void setWatching(bool);
	
	// function callers
  GSPattern *  getNewPattern();
  void callSetupFunction();
	GSPattern * callTimeChanged(double time);
	void buildParamsFromScript();
	
	// python wrapper object
  PythonWrap  py ;
	
	
  File pythonFile;
  class Listener{
  public:
    virtual ~Listener(){};
    virtual void newFileLoaded(const File & f){};
		virtual void newPatternLoaded( GSPattern * p){};
		virtual void newParamsLoaded( OwnedArray<PyJUCEParameter> *){};
  };
  ListenerList<Listener> listeners;
  void addListener(Listener * l){listeners.add(l);}
  void removeListener(Listener * l){listeners.remove(l);}
	void timeChanged(double time) override;
	
	OwnedArray<PyJUCEParameter> params;
	
protected:
	
  void timerCallback()override;
  Time lastPythonFileMod;
	
	PyObject * timePyObj ;
	PyObject *timeKey;
	
  GSPatternPyWrap GSPatternWrap;
	
	
	
};


#endif  // PYJUCEAPI_H_INCLUDED
