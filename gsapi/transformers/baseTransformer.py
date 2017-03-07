from __future__ import absolute_import, division, print_function


class BaseTransformer(object):
    """Base class for defining a transform algorithm.

    Such class needs to provide the following functions:
        - configure: configure current transformer based on implementation
        specific parameters passed in the dict argument
        - transformPattern: return a transformed version of Pattern
    """

    def __init__(self):
        self.type = "None"

    def configure(self, paramDict):
        """Configure the current transformer based on implementation
        specific parameters passed in paramDict argument.

        Args:
            paramDict: a dictionary with configuration values.
        """
        raise NotImplementedError("Not Implemented.")

    def transformPattern(self, pattern):
        """Return a transformed pattern

        Args:
            pattern: the Pattern to be transformed.
        """
        raise NotImplementedError("Not Implemented.")
