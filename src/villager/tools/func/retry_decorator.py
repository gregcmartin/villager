import functools
import time
import logging

import loguru


def retry(max_retries=3, delay=1):
    """
    重试装饰器

    参数:
    max_retries (int): 最大重试次数。
    delay (int): 重试间隔时间（秒）。
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_retries:
                        loguru.logger.error(f"Function {func.__name__} failed with {e} after {attempts} attempts.")
                        raise
                    loguru.logger.warning(f"Function {func.__name__} failed with {e}. Retrying in {delay} seconds.")
                    loguru.logger.trace(e)
                    time.sleep(delay)

        return wrapper

    return decorator
