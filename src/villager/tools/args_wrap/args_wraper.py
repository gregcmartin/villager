import base64
import pickle


def serialize_args(*args, **kwargs):
    """
    Serialize the output of args and kwargs into bytecode, then return the base64 encoding
    :param args:
    :param kwargs:
    :return: Serialized args and kwargs
    """
    return base64.b64encode(pickle.dumps((args, kwargs))).decode('utf-8')


def deserialize_args(serialized_args):
    """
    Deserialize the serialized args and kwargs
    :param serialized_args:
    :return: Deserialized args and kwargs
    """
    return pickle.loads(base64.b64decode(serialized_args))


def deserialize_args_decorator(func):
    """
    Deserialize the serialized args and kwargs
    :param func:
    :return: A wrapper function that deserializes the args and kwargs
    """

    def wrapper(serialized_args):
        args, kwargs = deserialize_args(serialized_args)
        return func(*args, **kwargs)

    return wrapper
