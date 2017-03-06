#include <boost/python.hpp>
#include "Pattern.h"

using namespace boost::python;

BOOST_PYTHON_MODULE(Pattern)
{
    class_<Pattern>("Pattern")
        .def_readwrite("originBPM", &Pattern::originBPM)
        .def_readwrite("duration", &Pattern::duration)
        .def_readwrite("timeSigNumerator", &Pattern::timeSigNumerator)
        .def_readwrite("timeSigDenominator",&Pattern::timeSigDenominator)
    ;
};
