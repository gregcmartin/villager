class NoSuchRAGLFileException(Exception):
    def __init__(self, message):
        """
        Exception raised when the RAGL file does not exist.
        :param message:
        """
        super().__init__(message)
