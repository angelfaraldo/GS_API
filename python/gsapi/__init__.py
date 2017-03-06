"""
The gsapi is a Python/C++ library for manipulating musical symbolic data.
All modules are documented, for more info on the given module type:

>> help(gsapi.modulename)

online tutorials and documentation:
    https://angelfaraldo.github.io/gsapi

source code:
    https://github.com/angefaraldo/gsapi
"""

from __future__ import absolute_import, division, print_function

from python.gsapi.version import *
from .patterns import pattern, event

#from python.gsapi.bassmine import BassmineMarkov
# from python.gsapi.patterns import patternUtils
# from python.gsapi.utils.Dataset import Dataset



if __name__ == '__main__':
    p = pattern()
    p.addEvent(event(0, 2, 60, 100))
    p.addEvent(event(1, 1, 60, 100))
    # logger.setLevel(level=logging.ERROR)
    # logger.warning(p.duration)
