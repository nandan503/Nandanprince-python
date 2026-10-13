"""
Reusable Exception Decorators Module
====================================
Provides decorators for wrapping functions with automated exception logging,
error traceback persistence, and controlled fallback recovery.
"""

from functools import wraps
import logging
from typing import Any, Callable, Optional, Tuple, Type

from error_logger import get_logger


def log_exceptions(
    expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    default_return: Any = None,
    user_message: Optional[str] = None,
    log_level: int = logging.ERROR,
):
    """
    Decorator that executes a function and catches specified expected exceptions.

    Behavior:
    1. Catches only instances of `expected_exceptions`. Unrelated exceptions are not suppressed.
    2. Logs the failure at `log_level` using `logger.exception()`, capturing the complete traceback.
    3. Logs the safe fallback recovery event at `logging.INFO`.
    4. Returns `default_return` without crashing the application.

    :param expected_exceptions: Tuple of exception classes to intercept and handle.
    :param default_return: Fallback value to return upon exception.
    :param user_message: Context message describing the operation.
    :param log_level: Logging severity level for the caught exception.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()
            try:
                return func(*args, **kwargs)
            except expected_exceptions as exc:
                msg = user_message or f"Exception occurred while executing '{func.__name__}'"
                # Use logger.exception to log full traceback
                logger.log(log_level, "%s - %s: %s", msg, type(exc).__name__, exc, exc_info=True)
                logger.info(
                    "Fallback recovery executed for '%s': returning safe value [%s].",
                    func.__name__,
                    default_return,
                )
                return default_return
        return wrapper
    return decorator
