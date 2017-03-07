from __future__ import absolute_import, division, print_function


def strip_suffix(filename, suffix=None):
    """
    Strip off the suffix of the given filename or string. Extracted from madmom

    Args:
        filename : (str) Filename or string to strip.
        suffix : (str, optional) Suffix to be stripped off (e.g. '.txt' including the dot).

    Returns:
        filename: Filename or string without suffix.

    """
    if suffix is not None and filename.endswith(suffix):
        return filename[:-len(suffix)]
    return filename


def match_files(filename, match_list, suffix=None, match_suffix=None):
    """
    Match a filename or string against a list of other filenames or strings.

    Args:
        filename : (str) Filename or string to strip.
        match_list : (list) Match to this list of filenames or strings.
        suffix : (str, optional) Suffix of `filename` to be ignored.
        match_suffix: Match only files from `match_list` with this suffix.

    Returns:
        matches: (list) List of matched files.

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
    Returns a list of files in `path` matching the given `suffix` or filters
    the given list to include only those matching the given suffix.

    Args:
        path : (str or list) Path or list of files to be searched / filtered.
        suffix : (str, optional) Return only files matching this suffix.

    Returns:
        file_list: (list) List of files.

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
