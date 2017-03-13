# !/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function

import logging

# Library's full version name.
# Changing it will change version in pip and in the documentation.
GSAPI_FULL_VERSION = u'1.0.4'

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# The background is set with 40 plus the number of the color.
# The foreground with 30.
# These are the sequences need to get colored output:
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
COLORS = {'WARNING': YELLOW,
          'INFO': WHITE,
          'DEBUG': BLUE,
          'CRITICAL': YELLOW,
          'ERROR': RED}

# =============================================================================

def getGsapiFullVersion():
    """
    Helper to get the full version name.

    """
    return GSAPI_FULL_VERSION


def getGsapiShortVersion():
    """
    Helper to get the short version name.

    """
    return u'.'.join(GSAPI_FULL_VERSION.split('.')[:2])


class ColoredFormatter(logging.Formatter):

    def __init__(self, msg):
        logging.Formatter.__init__(self, msg)

    def format(self, record):
        levelname = record.levelname
        if ColoredLogger.USE_COLOR_OUTPUT and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
            record.boldSeq = BOLD_SEQ
            record.resetSeq = RESET_SEQ
        else:
            record.boldSeq = ""
            record.resetSeq = ""

        return logging.Formatter.format(self, record)


class ColoredLogger(logging.Logger):
    """
    Custom logger class with multiple destinations.

    """
    USE_COLOR_OUTPUT = False
    FORMAT = "[%(boldSeq)s%(name)-15s%(resetSeq)s][%(levelname)-8s] % " \
             "(message)s (%(boldSeq)s%(filename)s%(resetSeq)s:%(lineno)d)"
    color_formatter = ColoredFormatter(FORMAT)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(color_formatter)

    def __init__(self, name):
        logging.Logger.__init__(self, name)
        return


def setDefaultLoggingLevel(level):
    """
    Sets the default log level if not defined inside each module.

    Parameters
    ----------
    level: str
        one of default python's logging levels:
        logging.[CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET]

    """
    gsapiLogger.setLevel(level)


def setUseColoredOutput(useColor):
    """
    Enable colored console output.

    Parameters
    ----------
    useColor: boolean
        Enable colored console output

    Notes
    -----
    It might be powerful in the console, but annoying otherwise.

    """
    ColoredLogger.USE_COLOR_OUTPUT = useColor

# =============================================================================

logging.setLoggerClass(ColoredLogger)
gsapiLogger = logging.getLogger("gsapi")

# The handler is only on the root to avoid logs duplicates
# while propagating to the root:

if not len(gsapiLogger.handlers):
    gsapiLogger.addHandler(ColoredLogger.consoleHandler)
else:
    # For debugging purpose this line can be commented out
    # However, when using local and global version of gsapi at the same time,
    # the following line is triggered some times:
    raise ImportError("Double import of logging, it should never happen!")
    pass

setDefaultLoggingLevel(logging.WARNING)
