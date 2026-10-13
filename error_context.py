"""
Context Manager for Error Handling
==================================
Provides a reusable context manager `ErrorContext` using `__enter__()`
and `__exit__()` for controlled execution, logging, and selective exception suppression.
"""

import logging
from typing import Optional, Tuple, Type

from error_logger import get_logger


class ErrorContext:
    """
    Context manager that encapsulates a block of risky code.

    Behavior:
    1. Logs entry and exit of the context.
    2. Catches exceptions occurring within the block.
    3. Logs the caught exception and its full traceback using `logger.exception()`.
    4. Suppresses the exception ONLY IF it matches `handle_exceptions` and `suppress` is True.
    5. Returns False from `__exit__()` for unhandled exceptions to avoid hiding programming bugs.
    """

    def __init__(
        self,
        context_name: str = "Execution Block",
        handle_exceptions: Tuple[Type[BaseException], ...] = (Exception,),
        suppress: bool = True,
        log_level: int = logging.ERROR,
    ):
        self.context_name = context_name
        self.handle_exceptions = handle_exceptions
        self.suppress = suppress
        self.log_level = log_level
        self.logger = get_logger()
        self.exception_caught: Optional[BaseException] = None

    def __enter__(self) -> "ErrorContext":
        self.logger.info("Entering protected context: '%s'", self.context_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_val is not None:
            self.exception_caught = exc_val

            # Check if this exception is configured to be handled
            if issubclass(exc_type, self.handle_exceptions):
                self.logger.log(
                    self.log_level,
                    "Exception handled in context '%s' - %s: %s",
                    self.context_name,
                    exc_type.__name__,
                    exc_val,
                    exc_info=True,
                )
                if self.suppress:
                    self.logger.info(
                        "Safely suppressed %s in context '%s'. Execution will continue.",
                        exc_type.__name__,
                        self.context_name,
                    )
                    return True  # Suppress the exception
                return False  # Propagate if suppress is False

            # Unhandled or unexpected exception type: log warning and let it propagate
            self.logger.warning(
                "Unhandled exception %s encountered in context '%s'. Propagating to caller.",
                exc_type.__name__,
                self.context_name,
                exc_info=True,
            )
            return False  # Do not suppress unrelated exceptions

        self.logger.info("Exited context '%s' successfully with no errors.", self.context_name)
        return False
