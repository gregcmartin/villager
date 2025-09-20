def append__doc__(func):
    """
    Append the docstring of the function to the return key
    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result, func.__doc__

    return wrapper
