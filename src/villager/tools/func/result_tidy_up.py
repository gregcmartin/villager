from functools import wraps

import loguru


def dedup_and_sort(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        def process(value):
            if isinstance(value, list):
                return sorted(set(value))
            return value

        if isinstance(result, tuple):
            return tuple(process(v) for v in result)
        else:
            return process(result)

    return wrapper


@dedup_and_sort
def example_function_single():
    return [3, 1, 2, 3, 1]


@dedup_and_sort
def example_function_multiple():
    return [3, 1, 2, 3, 1], [4, 5, 4, 6]


def example_function_single_no_sort():
    return [3, 1, 2, 3, 1]


def example_function_multiple_no_sort():
    return [3, 1, 2, 3, 1], [4, 5, 4, 6]


def example_int_return():
    return 123


def example_str_return():
    return 'abc'


@dedup_and_sort
def example_int_return_with_decorator():
    return 123


@dedup_and_sort
def example_str_return_with_decorator():
    return 'abc'


if __name__ == '__main__':
    loguru.logger.info(example_function_single_no_sort())
    loguru.logger.info(example_function_multiple_no_sort())
    loguru.logger.info('----以上为不排序的结果----')
    loguru.logger.info(example_function_single())
    loguru.logger.info(example_function_multiple())
    loguru.logger.info('----以上为排序的结果----')
    loguru.logger.info(example_int_return())
    loguru.logger.info(example_str_return())
    loguru.logger.info('----以上为不排序的结果----')
    loguru.logger.info(example_int_return_with_decorator())
    loguru.logger.info(example_str_return_with_decorator())
    loguru.logger.info('----以上为排序的结果----')