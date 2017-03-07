from __future__ import absolute_import, division, print_function

import logging

from . import bassmine, descriptors, styles, transformers
from . import io
from .logger import gsapiLogger
from .patterns.event import Event
from .patterns.pattern import Pattern
from .patterns.dataset import Dataset
from .version import *


if __name__ == '__main__':
    p = Pattern()
    p.addEvent(Event(0, 2, 60, 100))
    p.addEvent(Event(1, 1, 60, 100))
   # logger.setLevel(level=logging.ERROR)
   # logger.warning(p.duration)



