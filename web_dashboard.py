"""
Flask Web Dashboard for Python Error Logger
============================================
Provides a professional, responsive Flask web application for real-time
error logging inspection, structured JSON log streaming, and scenario execution.

Endpoints:
- GET  /                     -> Interactive Web Dashboard UI
- GET  /api/logs             -> Structured JSON log entries (parsed with tracebacks)
- GET  /api/summary          -> Diagnostic summary of error counts & severity levels
- GET  /api/download         -> Direct file download of active logs/app.log
- POST /api/trigger/<name>   -> Execute realistic error scenario
- POST /api/clear            -> Truncate log file
"""

import os
import re
from typing import Any, Dict, List, Optional
from flask import Flask, render_template, jsonify, send_file, request

from error_logger import get_logger, get_logger_manager
import scenarios

LOG_HEADER_REGEX = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| \[([A-Z]+)\s*\] \| (.*?:\d+ \([^\)]+\)) \| (.*)$"
)


def parse_log_entries(log_file_path: str) -> Dict[str, Any]:
    """
    Safely reads and parses a log file into structured JSON objects.
    Extracts timestamps, severity levels, code origins, messages, and stack traces.
    Handles missing files, empty files, and malformed entries gracefully.
    """
    if not os.path.exists(log_file_path):
        return {
            "status": "empty",
            "total_entries": 0,
            "logs": [],
            "message": f"Log file '{os.path.basename(log_file_path)}' does not exist yet.",
        }

    try:
        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as err:
        return {
            "status": "error",
            "total_entries": 0,
            "logs": [],
            "message": f"Unable to read log file: {err}",
        }

    if not lines:
        return {
            "status": "empty",
            "total_entries": 0,
            "logs": [],
            "message": "Log file is currently empty.",
        }

    entries: List[Dict[str, Any]] = []
    current_entry: Optional[Dict[str, Any]] = None
    traceback_lines: List[str] = []

    for line in lines:
        stripped_line = line.rstrip("\r\n")
        match = LOG_HEADER_REGEX.match(stripped_line)

        if match:
            # Finalize previous entry
            if current_entry is not None:
                if traceback_lines:
                    current_entry["traceback"] = "\n".join(traceback_lines).strip()
                entries.append(current_entry)
                traceback_lines = []

            timestamp, level, source, message = match.groups()
            current_entry = {
                "timestamp": timestamp,
                "level": level.strip(),
                "source": source.strip(),
                "message": message.strip(),
                "traceback": "",
            }
        else:
            # Continuation line (traceback or multi-line message)
            if current_entry is not None:
                traceback_lines.append(stripped_line)
            else:
                # Malformed leading entry
                if stripped_line.strip():
                    entries.append({
                        "timestamp": "N/A",
                        "level": "UNKNOWN",
                        "source": "malformed_entry",
                        "message": stripped_line,
                        "traceback": "",
                    })

    # Append trailing entry
    if current_entry is not None:
        if traceback_lines:
            current_entry["traceback"] = "\n".join(traceback_lines).strip()
        entries.append(current_entry)

    return {
        "status": "success",
        "total_entries": len(entries),
        "logs": entries,
    }


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Application factory for Flask web dashboard."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    if test_config:
        app.config.update(test_config)

    logger = get_logger()
    manager = get_logger_manager()

    @app.route("/")
    def dashboard():
        """Render the main interactive dashboard UI."""
        return render_template("index.html")

    @app.route("/api/logs", methods=["GET"])
    def get_logs():
        """
        Read-only JSON API endpoint returning parsed structured log entries.
        Includes timestamp, severity level, source file, message, and traceback.
        """
        log_path = app.config.get("LOG_FILE", manager.log_file)
        parsed_data = parse_log_entries(log_path)
        return jsonify(parsed_data)

    @app.route("/api/summary", methods=["GET"])
    def get_summary():
        """
        Read-only JSON summary endpoint for total entries and counts by severity level
        and exception classes.
        """
        log_path = app.config.get("LOG_FILE", manager.log_file)

        if not os.path.exists(log_path):
            return jsonify({
                "status": "empty",
                "total_entries": 0,
                "total_errors": 0,
                "levels": {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0},
                "error_types": {},
            })

        # Calculate metrics using ErrorLoggerManager analyzer
        stats = manager.get_summary_statistics()
        return jsonify({
            "status": "success",
            "total_entries": stats["TOTAL_ENTRIES"],
            "total_errors": stats["TOTAL_ERRORS"],
            "levels": {
                "DEBUG": stats["DEBUG"],
                "INFO": stats["INFO"],
                "WARNING": stats["WARNING"],
                "ERROR": stats["ERROR"],
                "CRITICAL": stats["CRITICAL"],
            },
            "error_types": stats.get("error_types", {}),
        })

    @app.route("/api/download", methods=["GET"])
    def download_log_file():
        """Downloads the active app.log file."""
        log_path = app.config.get("LOG_FILE", manager.log_file)
        if not os.path.exists(log_path):
            return jsonify({"status": "error", "message": "Log file not found."}), 404

        return send_file(
            log_path,
            as_attachment=True,
            download_name="app.log",
            mimetype="text/plain",
        )

    @app.route("/api/trigger/<scenario_name>", methods=["POST"])
    def trigger_scenario(scenario_name: str):
        """Triggers a real exception scenario on demand."""
        scenario_map = {
            "zero_division": (
                lambda: scenarios.run_arithmetic_scenario(50, 0),
                "ZeroDivisionError triggered and logged",
            ),
            "file_not_found": (
                lambda: scenarios.run_file_system_scenario("missing_config_file.json"),
                "FileNotFoundError triggered and logged",
            ),
            "key_error": (
                lambda: scenarios.run_dictionary_lookup_scenario({"app_id": 101}, "auth_token"),
                "KeyError triggered and logged",
            ),
            "value_error": (
                lambda: scenarios.run_value_conversion_scenario("Invalid_Integer_String"),
                "ValueError triggered and logged",
            ),
            "index_error": (
                lambda: scenarios.run_list_index_scenario(["item1", "item2"], 99),
                "IndexError triggered and logged",
            ),
            "type_error": (
                lambda: scenarios.run_type_mismatch_scenario("Connection Port: ", 8080),
                "TypeError triggered and logged",
            ),
            "custom_db": (
                scenarios.run_decorator_scenario,
                "@log_exceptions fallback scenario triggered",
            ),
            "context_mgr": (
                scenarios.run_context_manager_scenario,
                "ErrorContext suppression scenario triggered",
            ),
        }

        if scenario_name not in scenario_map:
            return jsonify({"success": False, "message": f"Unknown scenario: '{scenario_name}'"}), 400

        action, description = scenario_map[scenario_name]
        action()
        return jsonify({"success": True, "message": description})

    @app.route("/api/clear", methods=["POST"])
    def clear_logs_endpoint():
        """Truncates the log file."""
        success = manager.clear_logs()
        return jsonify({"success": success, "message": "Log file cleared successfully."})

    return app


# Default app instance
app = create_app()


def start_server(host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    """Starts the Flask development server."""
    print("=" * 65)
    print("🚀 Python Error Logger - Flask Web Dashboard is LIVE!")
    print(f"🌐 Access Dashboard in Browser: http://{host}:{port}")
    print("=" * 65)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    start_server()
