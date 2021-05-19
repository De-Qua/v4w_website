"""
All the errors that can be thrown by the API
"""

from app.src.api import constants as cst


class CoordinatesFormatError(Exception):
    """Error to catch strings that don't match the coordinates format."""

    def __init__(self, coord):
        self.code = cst.INPUT_SHOULD_BE_COORDINATES
        self.coord = coord
        self.message = 'Input coordinates do not match the example format "12.339041,45.434268"'
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} - Input: {self.coord}"


class CoordinatesNumberError(Exception):
    """Error to catch if there are no two coordinates."""

    def __init__(self, coord):
        self.code = cst.NUMBER_COORDINATES
        self.message = 'You must give exactly two coordinates'
        super().__init__(self.message)


class NoPathFound(Exception):
    """Error to indicate that no path has been found."""

    def __init__(self, start, end):
        self.code = cst.NO_PATH_FOUND
        self.start = start
        self.end = end
        self.message = "No path found"
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} - Start: {self.start} End: {self.end}"
