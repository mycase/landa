"""Defines the exceptions used in the farcy package."""


class LandaException(Exception):

    """Farcy root exception class."""

    def __str__(self):
        """Return the exception's class name."""
        retval = super(LandaException, self).__str__()
        return retval or self.__class__.__name__
