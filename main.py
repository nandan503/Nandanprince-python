"""
Python Error Logger - Main Application Entrypoint
==================================================
Provides an interactive command-line interface (CLI) and script flags
to execute scenarios, view logs, inspect error summaries, run tests,
and clear logs with confirmation.

Usage:
    python3 main.py               # Interactive menu mode
    python3 main.py --demo        # Run all 8 demonstration scenarios
    python3 main.py --scenario 1  # Run individual scenario (1 to 8)
    python3 main.py --view        # View active app.log contents
    python3 main.py --summary     # Display error summary by exception type
    python3 main.py --test        # Run automated test suite
    python3 main.py --clear       # Clear app.log with prompt confirmation
"""

import sys
import os
import argparse
import unittest

from error_logger import get_logger, get_logger_manager
import scenarios

# Initialize central application logger
logger = get_logger()
manager = get_logger_manager()


def print_banner() -> None:
    """Displays application banner."""
    print("""
========================================================================
🛡️  PYTHON ERROR LOGGER - REAL-TIME DIAGNOSTIC SYSTEM
========================================================================
 Built with Python's built-in 'logging' module.
 Real-time console streaming & structured logging in 'logs/app.log'.
========================================================================
""")


def display_log_contents(max_lines: int = 50) -> None:
    """Reads and formats the most recent lines from the active log file."""
    lines = manager.read_logs(max_lines=max_lines)
    if not lines:
        print(f"\n[Info] Log file '{manager.log_file}' is currently empty or does not exist.")
        return

    print(f"\n📜 Recent Log Entries ({manager.log_file}) [Showing last {len(lines)} lines]:")
    print("-" * 75)
    for line in lines:
        stripped = line.rstrip()
        # ANSI color-coding for readability in terminal
        if "[ERROR" in stripped:
            print(f"\033[91m{stripped}\033[0m")
        elif "[CRITICAL" in stripped:
            print(f"\033[95m\033[1m{stripped}\033[0m")
        elif "[WARNING" in stripped:
            print(f"\033[93m{stripped}\033[0m")
        elif "[INFO" in stripped:
            print(f"\033[92m{stripped}\033[0m")
        elif "[DEBUG" in stripped:
            print(f"\033[94m{stripped}\033[0m")
        else:
            print(stripped)
    print("-" * 75)


def display_error_summary() -> None:
    """Displays structured breakdown of errors and exception types."""
    stats = manager.get_summary_statistics()
    print("\n" + "=" * 50)
    print("📊 ERROR & LOG SUMMARY REPORT")
    print("=" * 50)
    print(f"Total Logged Entries : {stats['TOTAL_ENTRIES']}")
    print(f"Total Error Events   : {stats['TOTAL_ERRORS']} (ERROR: {stats['ERROR']}, CRITICAL: {stats['CRITICAL']})")
    print(f"Warnings             : {stats['WARNING']}")
    print(f"Informational Events : {stats['INFO']}")
    print(f"Debug Events         : {stats['DEBUG']}")

    print("\n[Severity Breakdown]")
    print("+" + "-" * 26 + "+" + "-" * 10 + "+")
    print(f"| {'Severity Level':<24} | {'Count':<8} |")
    print("+" + "-" * 26 + "+" + "-" * 10 + "+")
    for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        print(f"| {lvl:<24} | {stats[lvl]:<8} |")
    print("+" + "-" * 26 + "+" + "-" * 10 + "+")

    print("\n[Exception Types Breakdown]")
    error_types = stats.get("error_types", {})
    if error_types:
        print("+" + "-" * 32 + "+" + "-" * 10 + "+")
        print(f"| {'Exception Class':<30} | {'Count':<8} |")
        print("+" + "-" * 32 + "+" + "-" * 10 + "+")
        for exc_name, count in sorted(error_types.items(), key=lambda item: -item[1]):
            print(f"| {exc_name:<30} | {count:<8} |")
        print("+" + "-" * 32 + "+" + "-" * 10 + "+")
    else:
        print("  No exception tracebacks recorded in log file yet.")
    print("=" * 50 + "\n")


def prompt_clear_logs(force: bool = False) -> None:
    """Prompts user for confirmation before clearing the log file."""
    if not force:
        confirm = input(f"\nAre you sure you want to clear '{manager.log_file}'? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Operation canceled. Log file was not cleared.")
            return

    if manager.clear_logs():
        print(f"Successfully cleared '{manager.log_file}'.")
    else:
        print("Failed to clear log file.")


def run_unit_tests() -> None:
    """Executes the automated test suite."""
    print("\n🧪 Running Automated Unit Tests...")
    suite = unittest.defaultTestLoader.discover(
        start_dir=os.path.join(os.path.dirname(__file__), "tests"),
        pattern="test_*.py",
    )
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


def run_single_scenario_interactive() -> None:
    """Sub-menu allowing execution of an individual scenario."""
    while True:
        print("\nSelect an Individual Scenario:")
        print("  1) ➗ Arithmetic Test (ZeroDivisionError)")
        print("  2) 📁 File System Test (FileNotFoundError)")
        print("  3) 🔑 Dictionary Lookup Test (KeyError)")
        print("  4) 📋 List Index Test (IndexError)")
        print("  5) 🔢 Value Conversion Test (ValueError)")
        print("  6) 🔀 Type Mismatch Test (TypeError)")
        print("  7) 🛡️ Decorator Test (@log_exceptions Fallback)")
        print("  8) 📦 Context Manager Test (ErrorContext)")
        print("  0) ⬅️ Back to Main Menu")

        choice = input("\nEnter choice [0-8]: ").strip()

        if choice == "1":
            print("\n--- Running Arithmetic Test ---")
            scenarios.run_arithmetic_scenario(100, 5)
            scenarios.run_arithmetic_scenario(100, 0)
        elif choice == "2":
            print("\n--- Running File System Test ---")
            scenarios.run_file_system_scenario(__file__)
            scenarios.run_file_system_scenario("non_existent_config.json")
        elif choice == "3":
            print("\n--- Running Dictionary Lookup Test ---")
            scenarios.run_dictionary_lookup_scenario({"app_mode": "production"}, "app_mode")
            scenarios.run_dictionary_lookup_scenario({"app_mode": "production"}, "missing_key")
        elif choice == "4":
            print("\n--- Running List Index Test ---")
            scenarios.run_list_index_scenario(["Alpha", "Beta", "Gamma"], 1)
            scenarios.run_list_index_scenario(["Alpha", "Beta", "Gamma"], 10)
        elif choice == "5":
            print("\n--- Running Value Conversion Test ---")
            scenarios.run_value_conversion_scenario("1024")
            scenarios.run_value_conversion_scenario("NotAnInteger_XYZ")
        elif choice == "6":
            print("\n--- Running Type Mismatch Test ---")
            scenarios.run_type_mismatch_scenario(50, 150)
            scenarios.run_type_mismatch_scenario("Total Count: ", 50)
        elif choice == "7":
            print("\n--- Running Decorator Test ---")
            scenarios.run_decorator_scenario()
        elif choice == "8":
            print("\n--- Running Context Manager Test ---")
            scenarios.run_context_manager_scenario()
        elif choice == "0":
            break
        else:
            print("Invalid selection. Please choose a number between 0 and 8.")


def interactive_menu() -> None:
    """Main interactive menu loop. Safely handles invalid inputs without crashing."""
    print_banner()

    while True:
        try:
            print("\nMain Menu:")
            print("  1) 🚀 Run All 8 Demonstration Scenarios")
            print("  2) 🎯 Run an Individual Scenario")
            print("  3) 📜 View Log File ('app.log')")
            print("  4) 📊 View Error Summary by Exception Type")
            print("  5) 🧪 Run Automated Unit Tests")
            print("  6) 🌐 Launch Flask Web Dashboard")
            print("  7) 🧹 Clear Log File (with confirmation)")
            print("  0) 🚪 Exit Application")

            choice = input("\nEnter choice [0-7]: ").strip()

            if choice == "1":
                scenarios.run_all_scenarios()
            elif choice == "2":
                run_single_scenario_interactive()
            elif choice == "3":
                display_log_contents()
            elif choice == "4":
                display_error_summary()
            elif choice == "5":
                run_unit_tests()
            elif choice == "6":
                print("\nStarting Flask Web Dashboard...")
                from web_dashboard import start_server
                start_server()
            elif choice == "7":
                prompt_clear_logs()
            elif choice == "0":
                print("\nExiting Python Error Logger. Goodbye!")
                sys.exit(0)
            else:
                print(f"[Warning] '{choice}' is not a valid menu option. Please choose between 0 and 7.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user. Returning to menu (or enter 0 to exit).")
        except Exception as err:
            print(f"[System Alert] An unexpected error occurred in menu: {err}")


def main() -> None:
    """CLI argument parser entrypoint."""
    parser = argparse.ArgumentParser(
        description="Python Error Logger - Automated Exception & Logging System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--demo", action="store_true", help="Execute all 8 demonstration scenarios")
    parser.add_argument(
        "--scenario",
        type=int,
        choices=range(1, 9),
        help="Execute an individual scenario by number (1 to 8)",
    )
    parser.add_argument("--view", action="store_true", help="Display contents of the log file")
    parser.add_argument("--summary", action="store_true", help="Display summary of errors by exception type")
    parser.add_argument("--web", action="store_true", help="Launch the Flask web dashboard")
    parser.add_argument("--test", action="store_true", help="Run automated unit test suite")
    parser.add_argument("--clear", action="store_true", help="Clear log file contents")
    parser.add_argument("--force", action="store_true", help="Force action without interactive confirmation")

    args = parser.parse_args()

    if args.demo:
        scenarios.run_all_scenarios()
    elif args.scenario:
        scenario_map = {
            1: lambda: (scenarios.run_arithmetic_scenario(10, 2), scenarios.run_arithmetic_scenario(10, 0)),
            2: lambda: (scenarios.run_file_system_scenario(__file__), scenarios.run_file_system_scenario("missing.json")),
            3: lambda: (scenarios.run_dictionary_lookup_scenario({"k": 1}, "k"), scenarios.run_dictionary_lookup_scenario({"k": 1}, "m")),
            4: lambda: (scenarios.run_list_index_scenario([1, 2], 0), scenarios.run_list_index_scenario([1, 2], 9)),
            5: lambda: (scenarios.run_value_conversion_scenario("42"), scenarios.run_value_conversion_scenario("bad")),
            6: lambda: (scenarios.run_type_mismatch_scenario(1, 2), scenarios.run_type_mismatch_scenario("a", 1)),
            7: scenarios.run_decorator_scenario,
            8: scenarios.run_context_manager_scenario,
        }
        scenario_map[args.scenario]()
    elif args.view:
        display_log_contents()
    elif args.summary:
        display_error_summary()
    elif args.web:
        from web_dashboard import start_server
        start_server()
    elif args.test:
        run_unit_tests()
    elif args.clear:
        prompt_clear_logs(force=args.force)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
