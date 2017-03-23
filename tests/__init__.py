#!/usr/bin/env python
# encoding: utf-8

"""
This module contains tests.

"""

from __future__ import absolute_import, division, print_function

from .test_agnostic_density import *
from .test_descriptor import *
from .test_io import *
from .test_markov_pattern import *
from .test_pattern import *
from .test_styles import *
from .test_utils import *
from .test_viewpoint import *

if __name__ == "__main__":
    runTest(profile=False, getStat=False)
