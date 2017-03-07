/*
 ==============================================================================

 PatternPyWrap.h
 Created: 19 Jun 2016 6:52:28pm
 Author:  Martin Hermant

 ==============================================================================
 */

#ifndef GSPATTERNPYWRAP_H_INCLUDED
#define GSPATTERNPYWRAP_H_INCLUDED
#include "PythonUtils.h"


#include "Pattern.h"
#include "PatternEventPyWrap.h"


class PatternPyWrap{
public:

  PatternPyWrap(){
    NameObjName = PyFromString("name");
    DurationObjName = PyFromString("duration");
    EventsObjName = PyFromString("events");
    timeSignatureName =PyFromString("timeSignature");
    gsapiModule = nullptr;
    gsPatternType = nullptr;

  }

  PyObject * gsapiModule ;
  PyTypeObject * gsPatternType;


  ~PatternPyWrap(){
    Py_CLEAR(NameObjName);
    Py_CLEAR(DurationObjName);
    Py_CLEAR(EventsObjName);
    Py_CLEAR(timeSignatureName);
    
    Py_CLEAR(gsapiModule);
//    Py_DecRef(gsPatternType);
  }
  void init(){
    gsapiModule = PyImport_ImportModule("gsapi");
    PyObject * gsapiDict = PyModule_GetDict(gsapiModule);
    gsPatternType = (PyTypeObject*)PyDict_GetItemString(gsapiDict, "Pattern");
    eventWrap.gsPatternEventType = (PyTypeObject*)PyDict_GetItemString(gsapiDict, "GSPatternEvent");
//    Py_DecRef(gsapiDict);
    //
    //		Pattern p;
    //		p.name = "test";
    //		GeneratePyObj(&p);
  }

  Pattern* GenerateFromObj(PyObject* o,Pattern * original=nullptr){
    if(!o)return nullptr;
    PyObject ** obj = _PyObject_GetDictPtr(o);
    if(!obj){DBG("weird class passed back"); return nullptr;}
    PyObject * dict = *obj;

    Pattern * p = original;
    if(!PyDict_Check(dict)){DBG("no dict passed back"); return p;}
    if(p== nullptr){
      p = new Pattern();
    }
    {
      PyObject * n = PyDict_GetItem(dict, NameObjName);
      if(n){p->name = PyToString(n);}
    }
    {
      PyObject * n = PyDict_GetItem(dict, DurationObjName);
      if(n){p->duration = PyFloat_AsDouble(n);}
    }
    {
      PyObject * n = PyDict_GetItem(dict, timeSignatureName);
      if(n && PyList_GET_SIZE(n)==2){
        p->timeSigNumerator=  PyInt_AsLong( PyTuple_GetItem(n, 0));
        p->timeSigDenominator=  PyInt_AsLong( PyTuple_GetItem(n, 1));
      }
    }

    {
      PyObject * n = PyDict_GetItem(dict, EventsObjName);
      if(n){

        if(PyList_Check(n)){
          int size = PyList_GET_SIZE(n);
          p->events.resize(size);
          for(int i = 0 ; i < size ; i++){
            GSPatternEvent * e = eventWrap.GenerateFromObj(PyList_GET_ITEM(n, i));
            if(e){p->events[i] = e;}
            else{DBG("wrong event added");}
          }
        }
        else{DBG("weird events structure");}

      }

    }
    return p;
  }

  PyObject*  GeneratePyObj(Pattern * p,PyObject * existing=nullptr){
    if(!p)return nullptr;
    PyObject * res = existing;

    //		create one if needed
    if(res==nullptr){
      PyObject * dummyArg = PyTuple_New(0);
      res = PyObject_Call((PyObject*)gsPatternType,dummyArg,nullptr);
    }

    //		PyObject * dbg = PyObject_Dir(res);
    //		DBG(PyToString(dbg));

    if(PyObject_SetAttr(res, NameObjName, PyFromString(p->name.c_str()))==-1){DBG("can't set Name");};
    if(PyObject_SetAttr(res, DurationObjName, PyLong_FromDouble(p->duration))==-1){DBG("can't set Duration");};

    {
      PyObject * n = PyList_New(2);
      PyList_SetItem(n, 0, PyInt_FromLong(p->timeSigNumerator));
      PyList_SetItem(n, 1, PyInt_FromLong(p->timeSigDenominator));
      if(PyObject_SetAttr(res, timeSignatureName, n)==-1){DBG("can't set timesignature");};
      Py_DecRef(n);
    }

    {
      int evSize = p->events.size();
      PyObject * n = PyList_New(evSize);
      for(int i = 0 ; i < evSize ; i++){
        PyObject * e = eventWrap.generatePyObj(p->events[i]);
        if(e){PyList_SetItem(n, i, e);}
        else{DBG("can't generate pyObj for event");}
      }
      PyObject_SetAttr(res, EventsObjName, n);
      Py_DecRef(n);
    }

    return res;
  }

private:

  PyObject * NameObjName;
  PyObject * DurationObjName;
  PyObject * EventsObjName;
  PyObject * timeSignatureName;
  
  PatternEventPyWrap eventWrap;
};

#endif  // GSPATTERNPYWRAP_H_INCLUDED