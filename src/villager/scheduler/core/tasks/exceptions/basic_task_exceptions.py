# ****************************************************************************
# This file contains the basic exceptions for the tasks
# ****************************************************************************
class BasicTaskException(Exception):
    """
    Base exception for all task exceptions
    """
    def __init__(self, message):
        """
        :param message: The message of the exception
        """
        super().__init__(message)


class FixableTaskException(BasicTaskException):
    """
    Base exception for all fixable task exceptions
    """
    def __init__(self, message):
        """
        :param message: The message of the exception
        """
        super().__init__(message)


class UnfixableTaskException(BasicTaskException):
    """
    Base exception for all unfixable task exceptions
    """
    def __init__(self, message):
        """
        :param message: The message of the exception
        """
        super().__init__(message)
