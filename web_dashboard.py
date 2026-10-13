"""
Real-Time Web Dashboard for Python Error Logger
================================================
A self-contained local web server (built with Python's standard `http.server`)
providing an interactive HTML5, CSS3, and JavaScript UI.

Features:
- Live log monitoring and auto-polling
- Trigger real exception scenarios directly from the browser
- Live metrics: Total errors, severity breakdown, exception types
- Real-time search and severity filtering
- Zero external dependencies: pure standard Python, HTML, CSS, JS.

Usage:
    python3 web_dashboard.py          # Starts server at http://127.0.0.1:8000
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from error_logger import (
    ErrorLoggerManager,
    get_logger,
    get_logger_manager,
)
import scenarios
from exceptions import DatabaseConnectionError

PORT = 8000

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Error Logger - Web Dashboard</title>
    <style>
        :root {
            --bg-body: #090d16;
            --bg-card: rgba(22, 30, 46, 0.85);
            --border-card: #1e293b;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-red: #ef4444;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-purple: #a855f7;
            --terminal-bg: #030712;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        body {
            background-color: var(--bg-body);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Top Header */
        header {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            border-bottom: 1px solid var(--border-card);
            padding: 18px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-title h1 {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .header-badge {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.4);
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 12px;
            font-weight: 600;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        /* Metrics Bar */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            padding: 20px 30px;
        }

        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 12px;
            padding: 16px 20px;
            backdrop-filter: blur(10px);
            transition: transform 0.2s, border-color 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #334155;
        }

        .metric-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        .metric-value {
            font-size: 26px;
            font-weight: 700;
        }

        .metric-red { color: #f87171; }
        .metric-amber { color: #fbbf24; }
        .metric-green { color: #34d399; }
        .metric-blue { color: #60a5fa; }

        /* Main Workspace Split */
        .workspace {
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 20px;
            padding: 0 30px 30px 30px;
            flex: 1;
        }

        @media (max-width: 900px) {
            .workspace { grid-template-columns: 1fr; }
        }

        /* Control Panel */
        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .panel-header {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 8px;
            padding-bottom: 10px;
            border-bottom: 1px solid #1e293b;
        }

        .scenario-grid {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .btn-scenario {
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid #334155;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            text-align: left;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }

        .btn-scenario:hover {
            background: #2563eb;
            border-color: #3b82f6;
            color: white;
            transform: translateX(3px);
        }

        .btn-scenario.critical-trigger:hover {
            background: #dc2626;
            border-color: #ef4444;
        }

        .btn-scenario span.code-tag {
            font-family: monospace;
            font-size: 11px;
            background: rgba(0, 0, 0, 0.4);
            padding: 2px 6px;
            border-radius: 4px;
            color: #93c5fd;
        }

        /* Custom Emitter */
        .custom-form {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .form-row {
            display: flex;
            gap: 8px;
        }

        select, input[type="text"] {
            background: #0f172a;
            border: 1px solid #334155;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            outline: none;
        }

        select:focus, input[type="text"]:focus {
            border-color: var(--accent-blue);
        }

        .btn-action {
            background: var(--accent-blue);
            color: white;
            border: none;
            padding: 9px 14px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }

        .btn-action:hover { background: #1d4ed8; }
        .btn-danger { background: #b91c1c; }
        .btn-danger:hover { background: #991b1b; }
        .btn-secondary { background: #334155; }
        .btn-secondary:hover { background: #475569; }

        /* Exception Types Pill Container */
        .type-pill-container {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 4px;
        }

        .type-pill {
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
            font-size: 11px;
            font-family: monospace;
            padding: 3px 8px;
            border-radius: 12px;
        }

        /* Log Viewer Section */
        .viewer-container {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .viewer-toolbar {
            padding: 12px 18px;
            background: #0f172a;
            border-bottom: 1px solid #1e293b;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: space-between;
            align-items: center;
        }

        .toolbar-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .terminal-box {
            background: var(--terminal-bg);
            flex: 1;
            padding: 16px;
            overflow: auto;
            font-family: "Menlo", "Courier New", monospace;
            font-size: 12.5px;
            line-height: 1.6;
            max-height: 580px;
            white-space: pre-wrap;
            word-break: break-all;
        }

        /* Log Styling */
        .log-line { margin-bottom: 2px; }
        .log-debug { color: #38bdf8; }
        .log-info { color: #4ade80; }
        .log-warning { color: #facc15; }
        .log-error { color: #f87171; font-weight: bold; }
        .log-critical { color: #f43f5e; font-weight: bold; }
        .log-traceback { color: #fda4af; }
        .log-timestamp { color: #94a3b8; }

        /* Notification Toast */
        #toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #1e293b;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            border-left: 4px solid var(--accent-blue);
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            display: none;
            z-index: 1000;
            font-size: 13px;
        }
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="header-title">
            <span style="font-size: 24px;">🛡️</span>
            <div>
                <h1>Real-Time Python Error Logger</h1>
                <div style="font-size: 12px; color: var(--text-muted);">Interactive Exception Management & Monitoring</div>
            </div>
            <span class="header-badge">LIVE MONITOR</span>
        </div>
        <div class="header-actions">
            <button class="btn-action btn-secondary" onclick="exportLogs()">💾 Download Log</button>
            <button class="btn-action btn-danger" onclick="clearLogs()">🧹 Clear</button>
        </div>
    </header>

    <!-- Metrics Bar -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Total Log Entries</div>
            <div class="metric-value metric-blue" id="stat-total">0</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Errors</div>
            <div class="metric-value metric-red" id="stat-errors">0</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Warnings</div>
            <div class="metric-value metric-amber" id="stat-warnings">0</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Info Events</div>
            <div class="metric-value metric-green" id="stat-info">0</div>
        </div>
    </div>

    <!-- Workspace -->
    <div class="workspace">

        <!-- Left Controls -->
        <div class="panel">
            <div class="panel-header">
                <span>⚡</span>
                <span>Exception Simulator</span>
            </div>
            <p style="font-size: 12px; color: var(--text-muted);">
                Click to trigger genuine Python exceptions wrapped with try-except logging:
            </p>
            <div class="scenario-grid">
                <button class="btn-scenario" onclick="triggerScenario('zero_division')">
                    <span>➗ Zero Division Error</span>
                    <span class="code-tag">100 / 0</span>
                </button>
                <button class="btn-scenario" onclick="triggerScenario('file_not_found')">
                    <span>📁 File Not Found</span>
                    <span class="code-tag">open()</span>
                </button>
                <button class="btn-scenario" onclick="triggerScenario('key_error')">
                    <span>🔑 Missing Key (KeyError)</span>
                    <span class="code-tag">dict[k]</span>
                </button>
                <button class="btn-scenario" onclick="triggerScenario('value_error')">
                    <span>🔢 Value Conversion Error</span>
                    <span class="code-tag">int("abc")</span>
                </button>
                <button class="btn-scenario" onclick="triggerScenario('index_error')">
                    <span>📋 Index Out Of Bounds</span>
                    <span class="code-tag">arr[99]</span>
                </button>
                <button class="btn-scenario" onclick="triggerScenario('type_error')">
                    <span>🔀 Type Mismatch Error</span>
                    <span class="code-tag">str + int</span>
                </button>
                <button class="btn-scenario" onclick="triggerScenario('custom_db')">
                    <span>🗄️ Custom DB Outage</span>
                    <span class="code-tag">Custom</span>
                </button>
                <button class="btn-scenario critical-trigger" onclick="triggerScenario('uncaught')">
                    <span>💥 Uncaught Thread Exception</span>
                    <span class="code-tag">CRITICAL</span>
                </button>
            </div>

            <!-- Exception Types Summary -->
            <div class="panel-header" style="margin-top: 10px;">
                <span>📊</span>
                <span>Active Exception Types</span>
            </div>
            <div class="type-pill-container" id="type-pills">
                <span style="font-size: 12px; color: #64748b;">No exceptions logged yet.</span>
            </div>

            <!-- Custom Emitter -->
            <div class="panel-header" style="margin-top: 10px;">
                <span>✍️</span>
                <span>Emit Custom Log</span>
            </div>
            <div class="custom-form">
                <div class="form-row">
                    <select id="custom-level" style="width: 110px;">
                        <option value="INFO">INFO</option>
                        <option value="DEBUG">DEBUG</option>
                        <option value="WARNING">WARNING</option>
                        <option value="ERROR">ERROR</option>
                        <option value="CRITICAL">CRITICAL</option>
                    </select>
                    <input type="text" id="custom-msg" placeholder="Type log message..." style="flex: 1;" value="Health check OK">
                </div>
                <button class="btn-action" onclick="emitCustomLog()">Emit Log</button>
            </div>
        </div>

        <!-- Right Terminal Log Viewer -->
        <div class="viewer-container">
            <div class="viewer-toolbar">
                <div class="toolbar-group">
                    <label style="font-size: 12px; color: var(--text-muted);">Severity Filter:</label>
                    <select id="filter-level" onchange="renderLogs()" style="padding: 4px 8px;">
                        <option value="ALL">ALL LEVELS</option>
                        <option value="ERROR">ERROR only</option>
                        <option value="CRITICAL">CRITICAL only</option>
                        <option value="WARNING">WARNING only</option>
                        <option value="INFO">INFO only</option>
                        <option value="DEBUG">DEBUG only</option>
                    </select>
                </div>

                <div class="toolbar-group">
                    <input type="text" id="search-input" placeholder="🔍 Search logs..." onkeyup="renderLogs()" style="padding: 4px 10px; width: 170px;">
                    <label style="font-size: 12px; color: var(--text-muted); cursor: pointer; display: flex; align-items: center; gap: 4px;">
                        <input type="checkbox" id="auto-refresh" checked> Auto (1s)
                    </label>
                    <button class="btn-action btn-secondary" onclick="fetchLogs()" style="padding: 5px 10px; font-size: 12px;">🔄</button>
                </div>
            </div>

            <div class="terminal-box" id="terminal-content">
                Loading logs...
            </div>
        </div>

    </div>

    <!-- Toast Notification -->
    <div id="toast">Operation completed</div>

    <script>
        let cachedLines = [];

        function showToast(msg, isError = false) {
            const toast = document.getElementById("toast");
            toast.textContent = msg;
            toast.style.borderLeftColor = isError ? "#ef4444" : "#3b82f6";
            toast.style.display = "block";
            setTimeout(() => { toast.style.display = "none"; }, 3000);
        }

        async function fetchLogs() {
            try {
                const res = await fetch("/api/logs");
                const data = await res.json();
                cachedLines = data.lines;
                updateStats(data.stats);
                renderLogs();
            } catch (err) {
                console.error("Failed to load logs:", err);
            }
        }

        function updateStats(stats) {
            document.getElementById("stat-total").textContent = stats.TOTAL_ENTRIES || 0;
            document.getElementById("stat-errors").textContent = (stats.TOTAL_ERRORS || (stats.ERROR + stats.CRITICAL)) || 0;
            document.getElementById("stat-warnings").textContent = stats.WARNING || 0;
            document.getElementById("stat-info").textContent = stats.INFO || 0;

            const pillContainer = document.getElementById("type-pills");
            pillContainer.innerHTML = "";
            const types = stats.error_types || {};
            const keys = Object.keys(types);
            if (keys.length === 0) {
                pillContainer.innerHTML = '<span style="font-size: 12px; color: #64748b;">No exceptions logged yet.</span>';
            } else {
                keys.forEach(k => {
                    const span = document.createElement("span");
                    span.className = "type-pill";
                    span.textContent = `${k} (${types[k]})`;
                    pillContainer.appendChild(span);
                });
            }
        }

        function renderLogs() {
            const filter = document.getElementById("filter-level").value;
            const search = document.getElementById("search-input").value.toLowerCase();
            const container = document.getElementById("terminal-content");

            if (!cachedLines || cachedLines.length === 0) {
                container.innerHTML = '<span class="log-timestamp">Log file is currently empty. Trigger an error scenario to see entries.</span>';
                return;
            }

            let output = "";
            let currentBlockMatches = false;

            for (const line of cachedLines) {
                const isLevelHeader = /\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)/.test(line);

                if (isLevelHeader) {
                    const levelMatch = (filter === "ALL") || line.includes(`[${filter}`);
                    const searchMatch = !search || line.toLowerCase().includes(search);
                    currentBlockMatches = levelMatch && searchMatch;
                }

                if (currentBlockMatches) {
                    let className = "log-line";
                    if (line.includes("[DEBUG")) className += " log-debug";
                    else if (line.includes("[INFO")) className += " log-info";
                    else if (line.includes("[WARNING")) className += " log-warning";
                    else if (line.includes("[ERROR")) className += " log-error";
                    else if (line.includes("[CRITICAL")) className += " log-critical";
                    else if (line.includes("Traceback") || line.includes("File \\"") || line.includes("line ")) className += " log-traceback";

                    // Escape HTML
                    const safeLine = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                    output += `<div class="${className}">${safeLine}</div>`;
                }
            }

            container.innerHTML = output || '<span class="log-timestamp">No log entries matched your filter/search criteria.</span>';
        }

        async function triggerScenario(name) {
            try {
                const res = await fetch(`/api/trigger/${name}`, { method: "POST" });
                const data = await res.json();
                showToast(`Triggered: ${name} -> ${data.message}`, true);
                fetchLogs();
            } catch (e) {
                showToast(`Failed to trigger: ${e}`, true);
            }
        }

        async function emitCustomLog() {
            const level = document.getElementById("custom-level").value;
            const message = document.getElementById("custom-msg").value;
            if (!message) return;

            try {
                await fetch("/api/emit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ level, message })
                });
                showToast(`Emitted [${level}] log.`);
                fetchLogs();
            } catch (e) {
                showToast(`Error emitting log: ${e}`, true);
            }
        }

        async function clearLogs() {
            if (!confirm("Are you sure you want to clear all contents of app.log?")) return;
            try {
                await fetch("/api/clear", { method: "POST" });
                showToast("app.log cleared successfully.");
                fetchLogs();
            } catch (e) {
                showToast(`Clear failed: ${e}`, true);
            }
        }

        function exportLogs() {
            window.open("/api/download", "_blank");
        }

        // Auto Refresh Loop
        setInterval(() => {
            if (document.getElementById("auto-refresh").checked) {
                fetchLogs();
            }
        }, 1200);

        // Initial Load
        fetchLogs();
    </script>
</body>
</html>
"""


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the Web Dashboard and API."""

    def log_message(self, format, *args):
        # Suppress noisy HTTP request console logging to keep terminal clean
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif path == "/api/logs":
            logger_mgr = get_logger_manager()
            lines = logger_mgr.read_logs()
            stats = logger_mgr.get_summary_statistics()
            payload = json.dumps({"lines": lines, "stats": stats})

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))

        elif path == "/api/download":
            logger_mgr = get_logger_manager()
            content = "".join(logger_mgr.read_logs())

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Disposition", "attachment; filename=\"app.log\"")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        logger_mgr = get_logger_manager()
        logger = get_logger()

        if path.startswith("/api/trigger/"):
            scenario_name = path.replace("/api/trigger/", "")
            msg = "Executed"

            if scenario_name == "zero_division":
                scenarios.run_arithmetic_scenario(100, 0)
                msg = "ZeroDivisionError handled and logged"
            elif scenario_name == "file_not_found":
                scenarios.run_file_system_scenario("missing_config_token.env")
                msg = "FileNotFoundError handled and logged"
            elif scenario_name == "key_error":
                scenarios.run_dictionary_lookup_scenario({"user": "dev"}, "jwt_token")
                msg = "KeyError handled and logged"
            elif scenario_name == "value_error":
                scenarios.run_value_conversion_scenario("InvalidHexCode_FF")
                msg = "ValueError handled and logged"
            elif scenario_name == "index_error":
                scenarios.run_list_index_scenario(["srv1", "srv2"], 10)
                msg = "IndexError handled and logged"
            elif scenario_name == "type_error":
                scenarios.run_type_mismatch_scenario("Error Count: ", 42)
                msg = "TypeError handled and logged"
            elif scenario_name == "custom_db":
                scenarios.run_decorator_scenario()
                msg = "Decorator fallback handled and logged"
            elif scenario_name == "uncaught":
                scenarios.run_context_manager_scenario()
                msg = "Context manager handled and logged"

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": msg}).encode("utf-8"))

        elif path == "/api/emit":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            try:
                data = json.loads(post_body.decode("utf-8"))
                lvl = data.get("level", "INFO").upper()
                msg = data.get("message", "Custom emitted message")

                lvl_map = {
                    "DEBUG": logger.debug,
                    "INFO": logger.info,
                    "WARNING": logger.warning,
                    "ERROR": logger.error,
                    "CRITICAL": logger.critical,
                }
                lvl_map.get(lvl, logger.info)(msg)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()

        elif path == "/api/clear":
            logger_mgr.clear_logs()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


def start_server(port: int = PORT):
    server_address = ("", port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print("=" * 65)
    print(f"🚀 Python Error Logger - Web Dashboard is LIVE!")
    print(f"🌐 Open in browser: http://127.0.0.1:{port}")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web dashboard server...")
        httpd.server_close()


if __name__ == "__main__":
    start_server()
