"""
Automated Test Suite for Python Error Logger
============================================
Validates scenarios, logging levels, traceback persistence, decorator fallback,
context manager suppression, and handler deduplication.
"""

import os
import unittest
import tempfile
import logging

from error_logger import ErrorLoggerManager, get_logger
import scenarios
from decorators import log_exceptions
from error_context import ErrorContext
from exceptions import DatabaseConnectionError


class TestPythonErrorLogger(unittest.TestCase):
    """Unit test cases for the Python Error Logger system."""

    def setUp(self):
        """Creates an isolated temporary log file environment for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_log_file = os.path.join(self.temp_dir.name, "test_app.log")

        # Reset singleton and initialize with isolated test log
        ErrorLoggerManager.reset_instance()
        self.manager = ErrorLoggerManager(
            log_file=self.test_log_file,
            console_output=False,
            log_level=logging.DEBUG,
        )
        self.logger = self.manager.logger

    def tearDown(self):
        """Cleans up temporary resources and resets logger singleton."""
        ErrorLoggerManager.reset_instance()
        self.temp_dir.cleanup()

    def test_log_file_created_automatically(self):
        """Verify that log file and directories are created automatically upon logging."""
        self.logger.info("Verifying automatic file creation.")
        self.assertTrue(os.path.exists(self.test_log_file))
        logs = self.manager.read_logs()
        self.assertTrue(any("Verifying automatic file creation." in line for line in logs))

    def test_reinitializing_logger_does_not_duplicate_messages(self):
        """Verify that calling get_logger multiple times does not leak duplicate handlers."""
        # Initialize multiple times
        logger1 = get_logger(log_file=self.test_log_file, console_output=False)
        logger2 = get_logger(log_file=self.test_log_file, console_output=False)

        # Emit single message
        logger2.info("Single distinct event test.")

        logs = self.manager.read_logs()
        matching_lines = [line for line in logs if "Single distinct event test." in line]
        self.assertEqual(len(matching_lines), 1, "Duplicate log handlers detected!")

    def test_successful_operations_do_not_generate_error_logs(self):
        """Verify that successful executions record INFO entries and 0 ERROR entries."""
        res_arith = scenarios.run_arithmetic_scenario(20, 4)
        self.assertEqual(res_arith, 5.0)

        res_conv = scenarios.run_value_conversion_scenario("500")
        self.assertEqual(res_conv, 500)

        res_dict = scenarios.run_dictionary_lookup_scenario({"status": "healthy"}, "status")
        self.assertEqual(res_dict, "healthy")

        stats = self.manager.get_summary_statistics()
        self.assertEqual(stats["ERROR"], 0, "Successful operations generated unexpected ERROR log entries!")
        self.assertGreater(stats["INFO"], 0)

    def test_arithmetic_zero_division_records_traceback(self):
        """Verify ZeroDivisionError is captured with full traceback details."""
        result = scenarios.run_arithmetic_scenario(10, 0)
        self.assertIsNone(result)

        logs = "".join(self.manager.read_logs())
        self.assertIn("[ERROR   ]", logs)
        self.assertIn("Failed arithmetic division", logs)
        self.assertIn("ZeroDivisionError: division by zero", logs)
        self.assertIn("Traceback (most recent call last):", logs)

    def test_file_not_found_records_traceback(self):
        """Verify FileNotFoundError is captured with full traceback details."""
        result = scenarios.run_file_system_scenario("non_existent_file_xyz.txt")
        self.assertIsNone(result)

        logs = "".join(self.manager.read_logs())
        self.assertIn("[ERROR   ]", logs)
        self.assertIn("FileNotFoundError", logs)
        self.assertIn("Traceback (most recent call last):", logs)

    def test_dictionary_key_error_records_traceback(self):
        """Verify KeyError is captured with full traceback details."""
        result = scenarios.run_dictionary_lookup_scenario({"key_a": 1}, "missing_key_b")
        self.assertIsNone(result)

        logs = "".join(self.manager.read_logs())
        self.assertIn("KeyError", logs)
        self.assertIn("missing_key_b", logs)

    def test_list_index_error_records_traceback(self):
        """Verify IndexError is captured with full traceback details."""
        result = scenarios.run_list_index_scenario([1, 2, 3], 99)
        self.assertIsNone(result)

        logs = "".join(self.manager.read_logs())
        self.assertIn("IndexError", logs)

    def test_value_error_records_traceback(self):
        """Verify ValueError is captured with full traceback details."""
        result = scenarios.run_value_conversion_scenario("NOT_AN_INTEGER")
        self.assertIsNone(result)

        logs = "".join(self.manager.read_logs())
        self.assertIn("ValueError", logs)

    def test_type_error_records_traceback(self):
        """Verify TypeError is captured with full traceback details."""
        result = scenarios.run_type_mismatch_scenario("String", 123)
        self.assertIsNone(result)

        logs = "".join(self.manager.read_logs())
        self.assertIn("TypeError", logs)

    def test_decorator_returns_fallback_and_logs_recovery(self):
        """Verify @log_exceptions returns configured fallback and logs recovery."""
        @log_exceptions(
            expected_exceptions=(DatabaseConnectionError,),
            default_return="SAFE_FALLBACK_DATA",
            user_message="Test DB Failure",
        )
        def faulty_db_call():
            raise DatabaseConnectionError("Connection timeout")

        output = faulty_db_call()
        self.assertEqual(output, "SAFE_FALLBACK_DATA")

        logs = "".join(self.manager.read_logs())
        self.assertIn("DatabaseConnectionError", logs)
        self.assertIn("Fallback recovery executed", logs)

    def test_context_manager_suppresses_configured_exception(self):
        """Verify ErrorContext suppresses only configured exceptions."""
        executed_after_suppression = False

        with ErrorContext("Test Context", handle_exceptions=(KeyError,), suppress=True):
            _ = {}["missing_key"]

        executed_after_suppression = True
        self.assertTrue(executed_after_suppression)

        logs = "".join(self.manager.read_logs())
        self.assertIn("Exception handled in context 'Test Context'", logs)
        self.assertIn("Safely suppressed KeyError", logs)

    def test_context_manager_propagates_unconfigured_exception(self):
        """Verify ErrorContext does NOT suppress unconfigured exceptions."""
        with self.assertRaises(ZeroDivisionError):
            with ErrorContext("Strict Context", handle_exceptions=(ValueError,), suppress=True):
                _ = 1 / 0

    def test_clear_logs_functionality(self):
        """Verify clear_logs truncates the log file."""
        self.logger.info("Entry before truncation.")
        self.assertGreater(len(self.manager.read_logs()), 0)

        cleared = self.manager.clear_logs()
        self.assertTrue(cleared)

        logs = self.manager.read_logs()
        # Contains 1 message indicating log was cleared
        self.assertEqual(len(logs), 1)
        self.assertIn("cleared successfully", logs[0])


if __name__ == "__main__":
    unittest.main()
