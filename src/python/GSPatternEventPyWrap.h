/*
  ==============================================================================

    GSPatternEventPyWrap.h
    Created: 19 Jun 2016 6:52:46pm
    Author:  Martin Hermant

  ==============================================================================
*/

#ifndef GSPATTERNEVENTPYWRAP_H_INCLUDED
#define GSPATTERNEVENTPYWRAP_H_INCLUDED

#include "PythonUtils.h"
#include "GSPatternEvent.h"


class GSPatternEventPyWrap{
public:

  GSPatternEventPyWrap(){
		
    StartObjName = PyFromString("startTime");
    DurationObjName = PyFromString("duration");
    PitchObjName = PyFromString("pitch");
    VelocityObjName = PyFromString("velocity");
    TagsObjName = PyFromString("tags");

    init();
  }
  ~GSPatternEventPyWrap(){
    Py_DECREF(TagsObjName);
    Py_DECREF(DurationObjName);
    Py_DECREF(StartObjName);
    Py_DECREF(PitchObjName);
    Py_DECREF(VelocityObjName);
  }

  void init(){


  }

  GSPatternEvent* GenerateFromObj(PyObject* o){
    GSPatternEvent * e = nullptr;
    PyObject ** obj = _PyObject_GetDictPtr(o);
    if(!obj){DBG("weird class passed back"); return nullptr;}
    PyObject * dict = *obj;
    if(!PyDict_Check(dict)){DBG("no dict passed back");}
    else{
      e = new GSPatternEvent();
      {
        PyObject * n = PyDict_GetItem(dict, StartObjName);
        if(n){e->start = PyFloat_AsDouble(n);}
      }
      {
        PyObject * n = PyDict_GetItem(dict, DurationObjName);
        if(n){e->duration = PyFloat_AsDouble(n);}
      }

      {
        PyObject * n = PyDict_GetItem(dict, PitchObjName);
        if(n){e->pitch = PyLong_AsLong(n);}
      }

      {
        PyObject * n = PyDict_GetItem(dict, VelocityObjName);
        if(n){e->velocity = PyLong_AsLong(n);}
      }
			{
        PyObject * n = PyDict_GetItem(dict, TagsObjName);
        if(n){
					if(PyList_Check(n)){
						e->eventTags.clear();
						int s = PyList_GET_SIZE(n);
						for(int i = 0 ; i < s; i++){
							PyObject * to = PyList_GET_ITEM(n,i);
							if(PyUnicode_Check(to)){to = PyUnicode_AsUTF8String(to);}
							if(PyString_Check(to)){e->eventTags.push_back(PyToString(to));}

							else{DBG("wrong type of tags : " << to->ob_type->tp_name);}
						}

					}
				}
      }

    }



    return e;
  }

  PyObject*  TagsObjName ;
  PyObject*  DurationObjName ;
  PyObject*  StartObjName ;
  PyObject*  PitchObjName ;
  PyObject*  VelocityObjName ;
  
  
};



#endif  // GSPATTERNEVENTPYWRAP_H_INCLUDED