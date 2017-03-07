#!/usr/bin/env python
# encoding: utf-8
"""This module contains tests."""

from __future__ import absolute_import, division, print_function


# Import all submodules
# from .test_agnostic_density import *
from . import test_agnostic_density
from .test_descriptor import *
from .test_io import *
from .test_markov_pattern import *
from .test_pattern import *
from .test_pattern_utils import *
from .test_styles import *
from .test_viewpoint import *

if __name__ == "__main__":
    # Run all tests:
    runTest(profile=False, getStat=False)
