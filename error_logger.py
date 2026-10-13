"""
Core Error Logger Module
========================
Configures Python's built-in `logging` module to provide real-time
console streaming and structured, UTF-8 encoded file logging in `logs/app.log`.

Format:
    %(asctime)s | [%(levelname)-8s] | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import re
from typing import Any, Dict, List, Optional

# Constants
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILENAME = "app.log"
DEFAULT_LOGGER_NAME = "PythonErrorLogger"
LOG_FORMAT = "%(asctime)s | [%(levelname)-8s] | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def resolve_log_path(log_path: Optional[str] = None) -> str:
    """
    Resolves the absolute path for the log file and ensures parent directory exists.
    Defaults to 'logs/app.log' in the project directory.
    """
    if log_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(base_dir, DEFAULT_LOG_DIR)
        os.makedirs(target_dir, exist_ok=True)
        return os.path.join(target_dir, DEFAULT_LOG_FILENAME)

    abs_path = os.path.abspath(log_path)
    parent_dir = os.path.dirname(abs_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    return abs_path


class ErrorLoggerManager:
    """
    Singleton manager responsible for creating and configuring the central
    application logger without duplicating handlers upon multiple initializations.
    """

    _instance: Optional["ErrorLoggerManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ErrorLoggerManager, cls).__new__(cls)
            cls._instance._is_configured = False
        return cls._instance

    def __init__(
        self,
        log_file: Optional[str] = None,
        logger_name: str = DEFAULT_LOGGER_NAME,
        log_level: int = logging.DEBUG,
        console_output: bool = True,
    ):
        if getattr(self, "_is_configured", False):
            return

        self.log_file = resolve_log_path(log_file)
        self.logger_name = logger_name
        self.log_level = log_level
        self.console_output = console_output

        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.log_level)
        self.logger.propagate = False

        self._configure_handlers()
        self._is_configured = True

    def _configure_handlers(self) -> None:
        """Configures file and console handlers, ensuring no duplicate handlers exist."""
        # Cleanly remove and close any existing handlers to prevent duplicates
        for existing_handler in self.logger.handlers[:]:
            existing_handler.close()
            self.logger.removeHandler(existing_handler)

        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        # 1. File Handler (UTF-8 encoded)
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB limit
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 2. Real-Time Console Handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def read_logs(self, max_lines: Optional[int] = None) -> List[str]:
        """Reads log lines from the active log file."""
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return lines[-max_lines:] if max_lines else lines
        except Exception as err:
            self.logger.error("Failed to read log file: %s", err)
            return [f"Error reading log file: {err}\n"]

    def clear_logs(self) -> bool:
        """Truncates the log file."""
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.truncate(0)
            self.logger.info("Log file '%s' cleared successfully.", os.path.basename(self.log_file))
            return True
        except Exception as err:
            self.logger.error("Failed to clear log file: %s", err)
            return False

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Analyzes the log file and returns counts of each severity level
        and breakdown of captured exception types.
        """
        stats: Dict[str, Any] = {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
            "TOTAL_ENTRIES": 0,
            "TOTAL_ERRORS": 0,
            "error_types": {},
        }

        lines = self.read_logs()
        exc_pattern = re.compile(r"^(?:[a-zA-Z0-9_]+\.)*([A-Z][a-zA-Z0-9_]*(?:Error|Exception)):")

        for line in lines:
            line_str = line.strip()

            # Check severity level
            for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                if f"[{level}" in line_str:
                    stats[level] += 1
                    stats["TOTAL_ENTRIES"] += 1
                    break

            # Check exception class in traceback
            match = exc_pattern.match(line_str)
            if match:
                exc_class = match.group(1)
                stats["error_types"][exc_class] = stats["error_types"].get(exc_class, 0) + 1

        stats["TOTAL_ERRORS"] = stats["ERROR"] + stats["CRITICAL"]
        return stats

    @classmethod
    def reset_instance(cls) -> None:
        """Resets the singleton instance (primarily for isolated test executions)."""
        if cls._instance is not None:
            for handler in cls._instance.logger.handlers[:]:
                handler.close()
                cls._instance.logger.removeHandler(handler)
        cls._instance = None


def get_logger(
    log_file: Optional[str] = None,
    console_output: bool = True,
    log_level: int = logging.DEBUG,
) -> logging.Logger:
    """Returns the central configured standard logging.Logger instance."""
    manager = ErrorLoggerManager(
        log_file=log_file,
        console_output=console_output,
        log_level=log_level,
    )
    return manager.logger


def get_logger_manager(log_file: Optional[str] = None) -> ErrorLoggerManager:
    """Returns the singleton ErrorLoggerManager instance."""
    return ErrorLoggerManager(log_file=log_file)
