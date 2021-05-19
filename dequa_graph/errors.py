"""
All the custom errors that can be thrown by the library
"""


class NoPathFound(Exception):
    """Error to indicate that no path has been found."""

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.message = "No path found"
        super().__init__(self.message)

    def __str__(self):
        return f"Start: {self.start} End: {self.end} -> {self.message}"


class MultipleSourcesError(Exception):
    """Error to indicate that multiple sources are given."""

    def __init__(self):
        self.message = "Path cannot be calculated from multiple sources"
        super().__init__(self.message)


class FormatError(Exception):
    """Error to indicate that there is an error in the format of the data."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
