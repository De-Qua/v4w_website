"""
All the errors that can be thrown by the API
"""


class CoordinatesError(ValueError):
    """Error to catch strings that don't match the coordinates format."""

    pass


class NoPathFound(Exception):
    """Error to indicate that no path has been found."""

    pass
