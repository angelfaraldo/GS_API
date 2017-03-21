# !/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

from . import gsdefs


def parallelCCompile(self, sources, output_dir=None, macros=None,
                     include_dirs=None, debug=0, extra_preargs=None,
                     extra_postargs=None, depends=None):

    # These lines are copied from distutils.ccompiler.CCompiler directly
    macros, objects, extra_postargs, pp_opts, build = \
        self._setup_compile(output_dir, macros, include_dirs,
                            sources, depends, extra_postargs)

    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)

    # number of parallel compilations
    n = 4

    import multiprocessing.pool

    def _single_compile(obj):
        try:
            src, ext = build[obj]
        except KeyError:
            return
        self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

    # convert to list, imap is evaluated on-demand:
    list(multiprocessing.pool.ThreadPool(n).imap(_single_compile, objects))
    return objects


def strip_suffix(filename, suffix=None):
    """
    Strip off the suffix of the given filename or string.
    Extracted from madmom

    Parameters
    ----------
    filename: str
        Filename or string to strip.
    suffix: str, optional
        Suffix to be stripped off (e.g. '.txt' including the dot).

    Returns
    -------
    filename: str
        Filename or string without suffix.

    """
    if suffix is not None and filename.endswith(suffix):
        return filename[:-len(suffix)]
    return filename


def match_files(filename, match_list, suffix=None, match_suffix=None):
    """
    Match a filename or string against a list of other filenames or strings.

    Parameters
    ----------
    filename: str
        Filename or string to strip.
    match_list: list
        Match to this list of filenames or strings.
    suffix: str, optional
        Suffix of `filename` to be ignored.
    match_suffix: str, optional
        Match only files from `match_list` with this suffix.

    Returns
    -------
    matches: list
        List of matched files.

    """
    import os
    import fnmatch

    # get the base name without the path
    basename = os.path.basename(strip_suffix(filename, suffix))
    # init return list
    matches = []
    # look for files with the same base name in the files_list
    if match_suffix is not None:
        pattern = "*%s*%s" % (basename, match_suffix)
    else:
        pattern = "*%s" % basename
    for match in fnmatch.filter(match_list, pattern):
        # base names must match exactly
        if basename == os.path.basename(strip_suffix(match, match_suffix)):
            matches.append(match)
    # return the matches
    return matches


def search_files(path, suffix=None):
    """
    Returns a list of files in `path` matching the given `suffix` or
    filters the given list to include only those matching the given suffix.

    Parameters
    ----------
    path: str or list
        Path or list of files to be searched / filtered.
    suffix: str, optional
        Return only files matching this suffix.

    Returns
    -------
    file_list: list
        List of files.

    """
    import os
    import glob

    # determine the files
    if isinstance(path, list):
        # a list of files or paths is given
        file_list = []
        # recursively call the function
        for f in path:
            file_list.extend(search_files(f, suffix))
    elif os.path.isdir(path):
        # use all files in the given path
        if suffix is None:
            file_list = glob.glob("%s/*" % path)
        elif isinstance(suffix, list):
            file_list = []
            for s in suffix:
                file_list.extend(glob.glob("%s/*%s" % (path, s)))
        else:
            file_list = glob.glob("%s/*%s" % (path, suffix))
    elif os.path.isfile(path):
        file_list = []
        # no matching needed
        if suffix is None:
            file_list = [path]
        # a list of suffices is given
        elif isinstance(suffix, list):
            for s in suffix:
                if path.endswith(s):
                    file_list = [path]
        # a single suffix is given
        elif path.endswith(suffix):
            file_list = [path]
    else:
        raise IOError("%s does not exist." % path)
    # remove duplicates
    file_list = list(set(file_list))
    # sort files
    file_list.sort()
    # return the file list
    return file_list


#  class PitchSpelling(object):
"""
This class implements utilities for the correct spelling of
notes and chords based on a representation by W. B. Hewlett.

|===========================================================|
| INTERVAL            DELTA       INTERVAL            DELTA |
|===========================================================|
| perfect unison      0           perfect octave      40    |
| augmented unison    1           diminished octave   39    |
|                                                           |
| diminished second   4           augmented seventh   36    |
| minor second        5           major seventh       35    |
| major second        6           minor seventh       34    |
| augmented second    7           diminished seventh  33    |
|                                                           |
| diminished third    10          augmented sixth     30    |
| minor third         11          major sixth         29    |
| major third         12          minor sixth         28    |
| augmented third     13          diminished sixth    27    |
|                                                           |
| diminished fourth   16          augmented fifth     24    |
| perfect fourth      17          perfect fifth       23    |
| augmented fourth    18          diminished fifth    22    |
|===========================================================|

- The inversion  of a simple interval is 40 minus that interval.

- Intervals may be computed across the B - C octave boundary
without extra calculations.

- Compound intervals such as tenths are related to intervals by
the difference of an octave (40). A major tenth is 12 + 40 = 52.

- Limitations: Intervals involving notes outside the set,
e.g. with three or integration sharps or flats, cannot be computed properly
from this representation. Some unusual intervals will have numbers
which overlap the numbers for the standard intervals given above.
For example,  the quadruple augmented unison between Cbb1 and C##1
has an interval value of 4, which also the number for a diminished
second. These limitations can be removed by using solutions of a
higher order.

Walter B. Hewlett (1992) "A Base-40 Number-line Representation
of Musical Pitch Notation." Musikometrica (4), pp. 1--14

"""

def pitch2name(pitch, pitchNames):
    """
    Converts a midi note number to alphabetic notation with octave index
    (e.g. "C4", "Db5")

    """
    octaveLength = len(pitchNames)
    octave = int(pitch / octaveLength) - 1
    note = pitch % octaveLength
    return str(pitchNames[note] + str(octave))


def makeChord(root, chord_structure):
    chord_structure = [0] + chord_structure
    for i in range(len(chord_structure)):
        root += chord_structure[i]
        chord_structure[i] = gsdefs.pitch40[root % 40]
    return chord_structure


def pc2note(pitch_class, alt="#"):
    if alt is "#":
        base40 = [2, 3, 8, 9, 14, 19, 20, 25, 26, 31, 32, 37]
    elif alt is "b":
        base40 = [2, 7, 8, 13, 14, 19, 24, 25, 30, 31, 36, 37]
    else:
        raise Exception("alt should be either '#' or 'b'")
    return gsdefs.pitch40[base40[pitch_class % 12]]


def pc2base40(pitch_class, alt="#"):
    if alt is "#":
        base40 = [2, 3, 8, 9, 14, 19, 20, 25, 26, 31, 32, 37]
    elif alt is "b":
        base40 = [2, 7, 8, 13, 14, 19, 24, 25, 30, 31, 36, 37]
    else:
        raise Exception("alt should be either '#' or 'b'")
    return base40[pitch_class % 12]
