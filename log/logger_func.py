from functools import wraps
import inspect


def log_func(logger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f'Функция {func.__name__} вызвана из функции {inspect.stack()[1][3]}')
            return func(*args, **kwargs)

        return wrapper
    return decorator
