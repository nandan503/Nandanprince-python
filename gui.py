"""
Python Error Logger - Interactive GUI Dashboard
================================================
A Tkinter-based graphical user interface for triggering common exceptions,
viewing real-time formatted logs with syntax coloring, filtering by severity,
and monitoring error statistics.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import Optional

from error_logger import (
    ErrorLoggerManager,
    get_logger,
    get_logger_manager,
)
import scenarios
from exceptions import DatabaseConnectionError


class ErrorLoggerGUI:
    """Tkinter Application for Python Error Logger."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Python Error Logger - Dashboard & Controller")
        self.root.geometry("1100, 720")
        self.root.minsize(850, 550)

        # Initialize core logging manager
        self.logger_mgr = get_logger_manager()
        self.logger = get_logger()

        # State tracking
        self.auto_refresh_enabled = tk.BooleanVar(value=True)
        self.current_filter = tk.StringVar(value="ALL")
        self.search_term = tk.StringVar(value="")

        self._configure_styles()
        self._build_ui()
        self._apply_text_tags()
        self.refresh_logs()
        self._schedule_auto_refresh()

    def _configure_styles(self):
        """Configure ttk styling."""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Color palette
        self.bg_color = "#f4f6f9"
        self.header_bg = "#1e293b"
        self.card_bg = "#ffffff"
        self.text_dark = "#0f172a"
        self.accent_blue = "#2563eb"
        self.accent_red = "#dc2626"
        self.border_color = "#cbd5e1"

        self.root.configure(bg=self.bg_color)

    def _build_ui(self):
        """Construct the overall application interface."""
        # Top Header Bar
        header_frame = tk.Frame(self.root, bg=self.header_bg, height=65)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            header_frame,
            text="🛡️ Python Error Logger Dashboard",
            font=("Helvetica", 18, "bold"),
            fg="#f8fafc",
            bg=self.header_bg,
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=12)

        subtitle_label = tk.Label(
            header_frame,
            text=f"Target: {os.path.basename(self.logger_mgr.log_file)}",
            font=("Helvetica", 11, "italic"),
            fg="#94a3b8",
            bg=self.header_bg,
        )
        subtitle_label.pack(side=tk.RIGHT, padx=20, pady=16)

        # Statistics Summary Bar
        self.stats_frame = tk.Frame(self.root, bg="#e2e8f0", height=38)
        self.stats_frame.pack(fill=tk.X, side=tk.TOP)

        self.stats_label = tk.Label(
            self.stats_frame,
            text="Loading log metrics...",
            font=("Helvetica", 11, "bold"),
            bg="#e2e8f0",
            fg="#1e293b",
        )
        self.stats_label.pack(side=tk.LEFT, padx=20, pady=6)

        # Main Split Container: Left (Controls), Right (Log Viewer)
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        # Left Control Panel
        left_frame = tk.Frame(main_paned, bg=self.card_bg, width=340, relief=tk.RIDGE, bd=1)
        main_paned.add(left_frame, weight=1)

        # Right Log Viewer Panel
        right_frame = tk.Frame(main_paned, bg=self.card_bg, relief=tk.RIDGE, bd=1)
        main_paned.add(right_frame, weight=3)

        self._build_control_panel(left_frame)
        self._build_viewer_panel(right_frame)

        # Bottom Status Bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready. Select any scenario above to simulate errors and log tracebacks.",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Helvetica", 10),
            bg="#ffffff",
            fg="#334155",
            padx=10,
            pady=4,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_control_panel(self, parent: tk.Frame):
        """Constructs buttons and triggers for error simulation."""
        header = tk.Label(
            parent,
            text="⚙️ Exception Simulator",
            font=("Helvetica", 13, "bold"),
            bg=self.card_bg,
            fg=self.text_dark,
        )
        header.pack(anchor=tk.W, padx=16, pady=(16, 8))

        desc = tk.Label(
            parent,
            text="Trigger real exceptions wrapped with\ntry-except blocks and logging hooks:",
            font=("Helvetica", 9),
            bg=self.card_bg,
            fg="#64748b",
            justify=tk.LEFT,
        )
        desc.pack(anchor=tk.W, padx=16, pady=(0, 12))

        # Scenario Buttons Frame
        btn_container = tk.Frame(parent, bg=self.card_bg)
        btn_container.pack(fill=tk.X, padx=16, pady=4)

        scenarios_list = [
            ("➗ Zero Division Error", self._trigger_zero_division, "#f8fafc", "#1e293b"),
            ("📁 File Not Found Error", self._trigger_file_not_found, "#f8fafc", "#1e293b"),
            ("🔑 Missing Key (KeyError)", self._trigger_key_error, "#f8fafc", "#1e293b"),
            ("🔢 Value Conversion Error", self._trigger_value_error, "#f8fafc", "#1e293b"),
            ("📋 Index Out of Bounds", self._trigger_index_error, "#f8fafc", "#1e293b"),
            ("🔀 Type Mismatch Error", self._trigger_type_error, "#f8fafc", "#1e293b"),
            ("🗄️ Database Connection Error", self._trigger_custom_db_error, "#f8fafc", "#1e293b"),
            ("💥 Uncaught Global Exception", self._trigger_uncaught_exception, "#fee2e2", "#991b1b"),
        ]

        for text, command, bg, fg in scenarios_list:
            btn = tk.Button(
                btn_container,
                text=text,
                command=command,
                bg=bg,
                fg=fg,
                font=("Helvetica", 10),
                relief=tk.GROOVE,
                anchor=tk.W,
                padx=10,
                pady=6,
                cursor="hand2",
            )
            btn.pack(fill=tk.X, pady=3)

        # Custom Logger Entry Section
        sep = ttk.Separator(parent, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=16, pady=16)

        custom_lbl = tk.Label(
            parent,
            text="📝 Custom Log Entry",
            font=("Helvetica", 12, "bold"),
            bg=self.card_bg,
            fg=self.text_dark,
        )
        custom_lbl.pack(anchor=tk.W, padx=16, pady=(0, 6))

        level_frame = tk.Frame(parent, bg=self.card_bg)
        level_frame.pack(fill=tk.X, padx=16, pady=2)
        tk.Label(level_frame, text="Severity:", font=("Helvetica", 9), bg=self.card_bg).pack(side=tk.LEFT)

        self.custom_level = ttk.Combobox(
            level_frame,
            values=["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=12,
        )
        self.custom_level.set("INFO")
        self.custom_level.pack(side=tk.RIGHT)

        self.custom_msg_entry = tk.Entry(parent, font=("Helvetica", 10), relief=tk.SOLID, bd=1)
        self.custom_msg_entry.insert(0, "System check: All services normal.")
        self.custom_msg_entry.pack(fill=tk.X, padx=16, pady=8)

        log_btn = tk.Button(
            parent,
            text="➕ Emit Custom Log",
            command=self._emit_custom_log,
            bg=self.accent_blue,
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor="hand2",
        )
        log_btn.pack(fill=tk.X, padx=16, pady=4)

    def _build_viewer_panel(self, parent: tk.Frame):
        """Constructs the log viewing area, toolbar, and filtering controls."""
        # Toolbar
        toolbar = tk.Frame(parent, bg="#f8fafc", height=45)
        toolbar.pack(fill=tk.X, side=tk.TOP, padx=8, pady=8)

        # Filter By Level
        tk.Label(toolbar, text="Filter:", font=("Helvetica", 10, "bold"), bg="#f8fafc").pack(side=tk.LEFT, padx=(4, 6))
        filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.current_filter,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=10,
        )
        filter_combo.pack(side=tk.LEFT, padx=4)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_logs())

        # Search Bar
        tk.Label(toolbar, text="Search:", font=("Helvetica", 10, "bold"), bg="#f8fafc").pack(side=tk.LEFT, padx=(12, 6))
        search_entry = tk.Entry(toolbar, textvariable=self.search_term, font=("Helvetica", 10), width=18)
        search_entry.pack(side=tk.LEFT, padx=4)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_logs())

        # Auto-refresh checkbox
        auto_chk = tk.Checkbutton(
            toolbar,
            text="Auto-refresh (2s)",
            variable=self.auto_refresh_enabled,
            bg="#f8fafc",
            font=("Helvetica", 9),
        )
        auto_chk.pack(side=tk.LEFT, padx=12)

        # Action Buttons on Right
        clear_btn = tk.Button(
            toolbar,
            text="🧹 Clear Log",
            command=self._confirm_clear_logs,
            bg="#fee2e2",
            fg="#991b1b",
            font=("Helvetica", 9, "bold"),
            relief=tk.GROOVE,
            padx=8,
            pady=3,
        )
        clear_btn.pack(side=tk.RIGHT, padx=4)

        export_btn = tk.Button(
            toolbar,
            text="💾 Export",
            command=self._export_logs,
            bg="#f1f5f9",
            font=("Helvetica", 9),
            relief=tk.GROOVE,
            padx=8,
            pady=3,
        )
        export_btn.pack(side=tk.RIGHT, padx=4)

        refresh_btn = tk.Button(
            toolbar,
            text="🔄 Refresh",
            command=self.refresh_logs,
            bg="#e0e7ff",
            fg="#3730a3",
            font=("Helvetica", 9, "bold"),
            relief=tk.GROOVE,
            padx=8,
            pady=3,
        )
        refresh_btn.pack(side=tk.RIGHT, padx=4)

        # Text Widget with Scrollbars for Log Content
        text_container = tk.Frame(parent, bg=self.card_bg)
        text_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        x_scrollbar = tk.Scrollbar(text_container, orient=tk.HORIZONTAL)
        y_scrollbar = tk.Scrollbar(text_container, orient=tk.VERTICAL)

        self.log_text = tk.Text(
            text_container,
            wrap=tk.NONE,
            font=("Menlo", 10) if sys.platform == "darwin" else ("Courier", 10),
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="white",
            xscrollcommand=x_scrollbar.set,
            yscrollcommand=y_scrollbar.set,
            padx=10,
            pady=10,
        )

        x_scrollbar.config(command=self.log_text.xview)
        y_scrollbar.config(command=self.log_text.yview)

        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _apply_text_tags(self):
        """Configure color tags for the syntax-highlighted log viewer."""
        self.log_text.tag_configure("TIMESTAMP", foreground="#94a3b8")
        self.log_text.tag_configure("DEBUG", foreground="#38bdf8")
        self.log_text.tag_configure("INFO", foreground="#4ade80")
        self.log_text.tag_configure("WARNING", foreground="#facc15")
        self.log_text.tag_configure("ERROR", foreground="#f87171", font=("Menlo", 10, "bold"))
        self.log_text.tag_configure("CRITICAL", foreground="#f43f5e", font=("Menlo", 10, "bold"))
        self.log_text.tag_configure("TRACEBACK", foreground="#fda4af")
        self.log_text.tag_configure("HIGHLIGHT", background="#374151")

    def refresh_logs(self):
        """Reads app.log, applies filters, formats colors, and updates metrics."""
        lines = self.logger_mgr.read_logs()
        target_level = self.current_filter.get().strip()
        search = self.search_term.get().strip().lower()

        # Update Statistics Label
        stats = self.logger_mgr.get_summary_statistics()
        self.stats_label.config(
            text=f"📊 Total Entries: {stats['TOTAL_ENTRIES']}  |  "
                 f"🔴 Errors: {stats['ERROR']}  |  "
                 f"💥 Critical: {stats['CRITICAL']}  |  "
                 f"⚠️ Warnings: {stats['WARNING']}  |  "
                 f"🟢 Info: {stats['INFO']}  |  "
                 f"🔵 Debug: {stats['DEBUG']}"
        )

        # Save previous scroll position
        yview_pos = self.log_text.yview()

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)

        if not lines:
            self.log_text.insert(tk.END, "Log file is currently empty. Run a scenario to generate entries.\n", "TIMESTAMP")
            self.log_text.config(state=tk.DISABLED)
            return

        # Filtering logic
        filtered_lines = []
        is_in_matching_block = False

        for line in lines:
            # Check if line is the start of a log entry
            has_level_marker = any(f"[{lvl}" in line for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

            if has_level_marker:
                level_match = (target_level == "ALL") or (f"[{target_level}" in line)
                search_match = (not search) or (search in line.lower())
                is_in_matching_block = level_match and search_match
            # If it's a traceback line (continuation of previous entry)
            elif is_in_matching_block and search:
                # also allow if search term matches the traceback
                is_in_matching_block = True

            if is_in_matching_block:
                filtered_lines.append(line)

        # Render colored text
        for line in filtered_lines:
            start_idx = self.log_text.index(tk.INSERT)
            self.log_text.insert(tk.END, line)
            end_idx = self.log_text.index(tk.INSERT)

            # Apply tags based on line contents
            if "[DEBUG" in line:
                self.log_text.tag_add("DEBUG", start_idx, end_idx)
            elif "[INFO" in line:
                self.log_text.tag_add("INFO", start_idx, end_idx)
            elif "[WARNING" in line:
                self.log_text.tag_add("WARNING", start_idx, end_idx)
            elif "[ERROR" in line:
                self.log_text.tag_add("ERROR", start_idx, end_idx)
            elif "[CRITICAL" in line:
                self.log_text.tag_add("CRITICAL", start_idx, end_idx)
            elif "Traceback" in line or "File \"" in line or "line " in line:
                self.log_text.tag_add("TRACEBACK", start_idx, end_idx)

        # Restore scroll or scroll to bottom if at bottom
        self.log_text.config(state=tk.DISABLED)
        if yview_pos[1] >= 0.95 or len(filtered_lines) < 20:
            self.log_text.see(tk.END)
        else:
            self.log_text.yview_moveto(yview_pos[0])

    def _schedule_auto_refresh(self):
        """Timer loop that calls refresh_logs every 2 seconds if enabled."""
        if self.auto_refresh_enabled.get():
            self.refresh_logs()
        self.root.after(2000, self._schedule_auto_refresh)

    def _set_status(self, message: str, is_error: bool = False):
        """Updates the status bar with feedback."""
        fg = "#b91c1c" if is_error else "#0f172a"
        self.status_bar.config(text=message, fg=fg)

    # -------------------------------------------------------------------------
    # Scenario Triggers
    # -------------------------------------------------------------------------
    def _trigger_zero_division(self):
        scenarios.run_arithmetic_scenario(42, 0)
        self._set_status("Triggered ZeroDivisionError (42 / 0). User alert shown; logged to app.log.", is_error=True)
        self.refresh_logs()

    def _trigger_file_not_found(self):
        scenarios.run_file_system_scenario("secret_system_vault.dat")
        self._set_status("Triggered FileNotFoundError ('secret_system_vault.dat'). Logged to app.log.", is_error=True)
        self.refresh_logs()

    def _trigger_key_error(self):
        scenarios.run_dictionary_lookup_scenario({"user_id": 101, "role": "admin"}, "jwt_auth_token")
        self._set_status("Triggered KeyError ('jwt_auth_token' missing). Logged to app.log.", is_error=True)
        self.refresh_logs()

    def _trigger_value_error(self):
        scenarios.run_value_conversion_scenario("AlphaNumeric_999")
        self._set_status("Triggered ValueError (int casting error). Logged to app.log.", is_error=True)
        self.refresh_logs()

    def _trigger_index_error(self):
        scenarios.run_list_index_scenario(["node_1", "node_2"], 99)
        self._set_status("Triggered IndexError (index 99 out of range). Logged to app.log.", is_error=True)
        self.refresh_logs()

    def _trigger_type_error(self):
        scenarios.run_type_mismatch_scenario("Database Port: ", 5432)
        self._set_status("Triggered TypeError (str + int). Logged to app.log.", is_error=True)
        self.refresh_logs()

    def _trigger_custom_db_error(self):
        scenarios.run_decorator_scenario()
        self._set_status("Triggered @log_exceptions decorator fallback. Logged to app.log.", is_error=True)
        self.refresh_logs()

    def _trigger_uncaught_exception(self):
        scenarios.run_context_manager_scenario()
        self._set_status("Triggered ErrorContext selective suppression. Recorded in app.log.", is_error=True)
        self.refresh_logs()
        """Simulates an unhandled exception in a worker thread to trigger threading.excepthook."""
        def faulty_worker():
            raise RuntimeError("Fatal unhandled runtime exception triggered from background worker thread!")

        worker_thread = threading.Thread(target=faulty_worker, name="SimulatedCrashingThread")
        worker_thread.start()
        worker_thread.join()
        self._set_status("Triggered Uncaught Exception via thread hook! Recorded as CRITICAL in app.log.", is_error=True)
        self.refresh_logs()

    def _emit_custom_log(self):
        lvl_str = self.custom_level.get().strip().upper()
        msg = self.custom_msg_entry.get().strip()
        if not msg:
            messagebox.showwarning("Empty Message", "Please enter a message to log.")
            return

        level_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CRITICAL": self.logger.critical,
        }
        log_fn = level_map.get(lvl_str, self.logger.info)
        log_fn(msg)
        self._set_status(f"Emitted custom {lvl_str} log message: '{msg}'")
        self.refresh_logs()

    def _confirm_clear_logs(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all contents of app.log?"):
            self.logger_mgr.clear_logs()
            self._set_status("Log file cleared.")
            self.refresh_logs()

    def _export_logs(self):
        export_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Export app.log to...",
        )
        if export_path:
            try:
                with open(self.logger_mgr.log_file, "r", encoding="utf-8") as src:
                    content = src.read()
                with open(export_path, "w", encoding="utf-8") as dst:
                    dst.write(content)
                messagebox.showinfo("Export Successful", f"Logs successfully exported to:\n{export_path}")
                self._set_status(f"Exported logs to {export_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export logs: {e}")


def launch_gui():
    """Launch the Tkinter application."""
    root = tk.Tk()
    app = ErrorLoggerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
