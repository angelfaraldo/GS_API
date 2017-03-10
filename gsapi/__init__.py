# from __future__ import absolute_import, division, print_function

# import logging

from . import bassmine, gsconfig, gsdefs, gsmarkov, gsio, gspattern, gsutil
from .descriptors import *
from .extractors import *
from .styles import *
from .transformers import *


#if __name__ == '__main__':
#    p = gspattern.Pattern()
#    p.addEvent(gspattern.Event(0, 2, 60, 100))
#    p.addEvent(gspattern.Event(1, 1, 60, 100))
#    gsconfig.logger.setLevel(level=logging.ERROR)
#    gsconfig.logger.warning(p.duration)
