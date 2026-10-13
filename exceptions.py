"""
Custom Application Exceptions Module
====================================
Defines custom exception classes used across the Python Error Logger system
for demonstrating domain-specific exception handling.
"""


class AppBaseException(Exception):
    """Base exception for all application-specific errors."""

    def __init__(self, message: str = "An application error occurred."):
        super().__init__(message)
        self.message = message


class DatabaseConnectionError(AppBaseException):
    """Raised when simulated database connection fails or times out."""

    def __init__(self, message: str = "Failed to establish database connection."):
        super().__init__(message)


class ResourceNotFoundError(AppBaseException):
    """Raised when an application resource or configuration file cannot be found."""

    def __init__(self, message: str = "Requested resource was not found."):
        super().__init__(message)


class ConfigurationError(AppBaseException):
    """Raised when invalid or missing configuration parameters are detected."""

    def __init__(self, message: str = "Invalid application configuration."):
        super().__init__(message)
