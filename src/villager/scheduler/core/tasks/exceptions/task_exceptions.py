# *****************************************************************************
# This file contains the exceptions that are raised by the tasks.
# *****************************************************************************
from scheduler.core.tasks.exceptions.basic_task_exceptions import FixableTaskException, UnfixableTaskException


class TaskTimeoutException(FixableTaskException):
    """
    Exception raised when a task times out
    """
    def __init__(self, message):
        """
        :param message: The message of the exception
        """
        super().__init__(message)


class TaskImpossibleException(UnfixableTaskException):
    """
    Exception raised when a task is impossible to complete
    """
    def __init__(self, message):
        """
        :param message: The message of the exception
        """
        super().__init__(message)


class TaskNeedTurningException(FixableTaskException):
    """
    Exception raised when a task needs to be turned
    """
    def __init__(self, message):
        """
        :param message: The message of the exception
        """
        super().__init__(message)
