"""Base exception classes and common exceptions for randomness tests."""

__all__ = [
    "TestError",
    "TestNotImplementedError",
    "TestInputError",
    "NonBinarySequenceError",
]


class TestError(Exception):
    """Base class for test-related errors"""


class TestNotImplementedError(TestError, NotImplementedError):
    """Error if test is not implemented to handle valid parameters"""


class TestInputError(TestError, ValueError):
    """Error if test cannot handle (invalud) parameters"""


class NonBinarySequenceError(TestInputError):
    """Error if sequence does not contain only 2 values"""

    def __str__(self):
        return "Sequence does not contain only 2 values (i.e. binary)"
