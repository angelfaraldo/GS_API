from __future__ import absolute_import, division, print_function


class BaseTransformer(object):
    """
    Base class for defining a transform algorithm.

    Methods
    -------
    configure: dict
        configure current transformer based on implementation specific parameters passed in the dict argument
    transformPattern: pattern
        return a transformed version of Pattern

    """

    def __init__(self):
        self.type = "None"

    def configure(self, paramDict):
        """
        Configure the current transformer based on implementation
        specific parameters passed in paramDict argument.

        Parameters
        ----------
        paramDict: dict
            a dictionary with configuration values.

        """
        raise NotImplementedError("Not Implemented.")

    def transformPattern(self, pattern):
        """
        Returns a transformed pattern.

        Parameters
        ----------
        pattern: pattern
            the pattern to be transformed.

        Returns
        -------
            a transformed pattern.
        """
        raise NotImplementedError("Not Implemented.")
