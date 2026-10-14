"""
Unit Tests for Flask Web Dashboard
==================================
Validates Flask routes, read-only JSON APIs, structured log parsing,
and robust handling of missing, empty, and malformed log files.
"""

import os
import unittest
import tempfile
import json

from web_dashboard import create_app, parse_log_entries


class TestFlaskWebDashboard(unittest.TestCase):
    """Test suite for the Flask web application."""

    def setUp(self):
        """Set up isolated temporary directory and test client."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sample_log_path = os.path.join(self.temp_dir.name, "test_app.log")

        # Create a sample log file with realistic entries and traceback
        with open(self.sample_log_path, "w", encoding="utf-8") as f:
            f.write(
                "2026-10-13 22:33:52 | [INFO    ] | scenarios.py:38 (run_arithmetic_scenario) | Attempting division: 50 / 5\n"
                "2026-10-13 22:33:52 | [ERROR   ] | scenarios.py:46 (run_arithmetic_scenario) | Failed division by zero\n"
                "Traceback (most recent call last):\n"
                "  File \"scenarios.py\", line 40, in run_arithmetic_scenario\n"
                "    result = a / b\n"
                "ZeroDivisionError: division by zero\n"
            )

        self.app = create_app({"TESTING": True, "LOG_FILE": self.sample_log_path})
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_dashboard_route_returns_200(self):
        """Verify GET / serves the HTML dashboard UI."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Python Error Logger Dashboard", response.data)

    def test_api_logs_returns_parsed_structured_json(self):
        """Verify GET /api/logs parses entries with timestamp, level, source, message, and traceback."""
        response = self.client.get("/api/logs")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_entries"], 2)

        # Inspect first entry (INFO)
        info_entry = data["logs"][0]
        self.assertEqual(info_entry["level"], "INFO")
        self.assertEqual(info_entry["timestamp"], "2026-10-13 22:33:52")
        self.assertIn("scenarios.py:38", info_entry["source"])
        self.assertEqual(info_entry["message"], "Attempting division: 50 / 5")
        self.assertEqual(info_entry["traceback"], "")

        # Inspect second entry (ERROR with traceback)
        error_entry = data["logs"][1]
        self.assertEqual(error_entry["level"], "ERROR")
        self.assertIn("Failed division by zero", error_entry["message"])
        self.assertIn("ZeroDivisionError: division by zero", error_entry["traceback"])
        self.assertIn("Traceback (most recent call last):", error_entry["traceback"])

    def test_api_summary_returns_counts_by_severity(self):
        """Verify GET /api/summary returns total entries and counts by severity."""
        response = self.client.get("/api/summary")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn("levels", data)
        self.assertIn("total_entries", data)
        self.assertIn("total_errors", data)
        self.assertIn("DEBUG", data["levels"])
        self.assertIn("INFO", data["levels"])
        self.assertIn("WARNING", data["levels"])
        self.assertIn("ERROR", data["levels"])
        self.assertIn("CRITICAL", data["levels"])

    def test_missing_log_file_handled_safely(self):
        """Verify non-existent log file returns safe empty status without 500 server crash."""
        missing_log_path = os.path.join(self.temp_dir.name, "does_not_exist.log")
        app_missing = create_app({"TESTING": True, "LOG_FILE": missing_log_path})
        client_missing = app_missing.test_client()

        response = client_missing.get("/api/logs")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "empty")
        self.assertEqual(data["total_entries"], 0)
        self.assertEqual(data["logs"], [])
        self.assertIn("does not exist", data["message"])

    def test_empty_log_file_handled_safely(self):
        """Verify empty log file (0 bytes) returns empty status gracefully."""
        empty_log_path = os.path.join(self.temp_dir.name, "empty.log")
        with open(empty_log_path, "w", encoding="utf-8") as f:
            pass  # create empty file

        app_empty = create_app({"TESTING": True, "LOG_FILE": empty_log_path})
        client_empty = app_empty.test_client()

        response = client_empty.get("/api/logs")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["status"], "empty")
        self.assertEqual(data["total_entries"], 0)
        self.assertEqual(data["logs"], [])

    def test_malformed_log_entries_handled_safely(self):
        """Verify malformed log lines that do not match the standard header are parsed safely."""
        malformed_log_path = os.path.join(self.temp_dir.name, "corrupt.log")
        with open(malformed_log_path, "w", encoding="utf-8") as f:
            f.write(
                "Random garbage line with no format\n"
                "Another corrupted line\n"
                "2026-10-13 22:33:52 | [INFO    ] | scenarios.py:10 (ok_fn) | Valid entry\n"
            )

        parsed = parse_log_entries(malformed_log_path)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["total_entries"], 3)
        self.assertEqual(parsed["logs"][0]["level"], "UNKNOWN")
        self.assertEqual(parsed["logs"][0]["message"], "Random garbage line with no format")
        self.assertEqual(parsed["logs"][2]["level"], "INFO")

    def test_trigger_scenario_endpoint(self):
        """Verify POST /api/trigger/<scenario> executes and returns success JSON."""
        response = self.client.post("/api/trigger/zero_division")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("ZeroDivisionError", data["message"])

    def test_invalid_scenario_returns_400(self):
        """Verify unknown scenario trigger returns 400 Bad Request."""
        response = self.client.post("/api/trigger/non_existent_scenario_123")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])

    def test_download_endpoint_sends_file(self):
        """Verify GET /api/download sends the log file as an attachment."""
        response = self.client.get("/api/download")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"run_arithmetic_scenario", response.data)


if __name__ == "__main__":
    unittest.main()
