from __future__ import absolute_import, division, print_function

from .AgnosticDensityTest import *
from .DescriptorTests import *
from .IOTest import *
from .MarkovPatternTest import *
from .PatternTest import *
from .PatternTestUtils import *
from .StylesTest import *
from .ViewpointTest import *


if __name__ == "__main__":
    # shortcut to run all tests:
    runTest(profile=False, getStat=False)
