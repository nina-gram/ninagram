"""
Contains all the exceptions of the library
"""

class StepNotFoundException(Exception):
    pass

class StateException(Exception):
    pass

class NoResultStateException(StateException):
    pass