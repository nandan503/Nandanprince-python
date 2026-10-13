# 🛡️ Clean & Professional Python Error Logger System

A complete, production-grade, and modular Python Error Logger system developed using Python's built-in `logging` module. Designed specifically for academic demonstrations, enterprise debugging, and clean error observability, this project automatically executes real test scenarios, captures genuine exceptions, displays user-friendly error alerts, and records structured diagnostic logs with full stack traces in `logs/app.log`.

---

## 📑 Table of Contents

- [1. System Overview](#1-system-overview)
- [2. Project Structure](#2-project-structure)
- [3. Core Architecture & Features](#3-core-architecture--features)
  - [3.1 Professional Logging Format](#31-professional-logging-format)
  - [3.2 User-Friendly Error Alerts](#32-user-friendly-error-alerts)
  - [3.3 Reusable Decorator (`@log_exceptions`)](#33-reusable-decorator-log_exceptions)
  - [3.4 Controlled Context Manager (`ErrorContext`)](#34-controlled-context-manager-errorcontext)
- [4. The Eight Demonstration Scenarios](#4-the-eight-demonstration-scenarios)
- [5. Installation & Execution Guide](#5-installation--execution-guide)
  - [Interactive Menu Mode](#interactive-menu-mode)
  - [Command-Line Arguments](#command-line-arguments)
- [6. Automated Unit Tests](#6-automated-unit-tests)
- [7. Real Execution Output](#7-real-execution-output)
- [8. Sample `logs/app.log` Output](#8-sample-logsapplog-output)
- [9. Academic & Technical Defense Highlights](#9-academic--technical-defense-highlights)

---

## 1. System Overview

This system demonstrates the best practices of Python exception handling and logging:
- **Zero Third-Party Runtime Dependencies**: Built entirely on standard Python modules (`logging`, `traceback`, `functools`, `unittest`, `os`, `sys`).
- **Real Exception Execution**: No simulated or hardcoded log strings. All errors stem from genuine Python runtime conditions.
- **Traceback Preservation**: Preserves original traceback information using `logger.exception()` / `exc_info=True`.
- **Dual-Stream Architecture**: Detailed diagnostic logs in UTF-8 file (`logs/app.log`) and clean real-time console feedback in `sys.stdout`.
- **Fault-Tolerant Execution**: Handled errors do not crash the demonstration runner; execution safely proceeds.
- **Handler Deduplication**: Uses a singleton pattern ensuring multiple calls to `get_logger()` never duplicate logging handlers or leak memory.

---

## 2. Project Structure

```text
python-error-logger/
├── main.py                 # Application entrypoint & interactive menu CLI
├── error_logger.py         # Central logger manager, UTF-8 file handler, and stats analyzer
├── scenarios.py            # Eight realistic error & success scenario handlers
├── decorators.py           # Reusable @log_exceptions decorator with fallback recovery
├── error_context.py        # ErrorContext manager supporting selective suppression
├── exceptions.py           # Custom domain exception classes
├── tests/
│   └── test_scenarios.py   # Automated unit test suite (13 passing test cases)
├── logs/
│   └── app.log             # Generated log file recording tracebacks & timestamps
├── requirements.txt        # Dependency specification (standard library)
└── README.md               # Complete project documentation & guide
```

---

## 3. Core Architecture & Features

### 3.1 Professional Logging Format

All logs follow the standardized enterprise format:

```text
%(asctime)s | [%(levelname)-8s] | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s
```

- **Date and Time**: ISO timestamp (`YYYY-MM-DD HH:MM:SS`).
- **Severity Level**: Aligned to 8 characters (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- **Code Origin**: Source file name and exact line number.
- **Function Name**: Enclosing function name.
- **Message**: Operational description, accompanied by full stack trace for exceptions.

### 3.2 User-Friendly Error Alerts

Technical tracebacks are reserved for the log file while end-users receive clean, non-technical alerts:

| Exception Type | User Alert Message |
|---|---|
| `ZeroDivisionError` | `[User Alert] Calculation Error: Division by zero is not permitted.` |
| `FileNotFoundError` | `[User Alert] File Error: The specified file could not be found.` |
| `KeyError` | `[User Alert] Data Error: The requested dictionary key was not found.` |
| `IndexError` | `[User Alert] Index Error: The requested list position is out of bounds.` |
| `ValueError` | `[User Alert] Input Error: The supplied value cannot be converted to an integer.` |
| `TypeError` | `[User Alert] Type Error: The supplied data types cannot be used in this operation.` |

*Privacy Guarantee: Passwords, authorization tokens, and confidential connection secrets are never printed in user alerts.*

### 3.3 Reusable Decorator (`@log_exceptions`)

Defined in `decorators.py`, this decorator intercepts specified expected exceptions:
- Catches only configured exception types (e.g. `expected_exceptions=(DatabaseConnectionError,)`). Unrelated errors are not suppressed.
- Records the full traceback via `logger.exception()`.
- Logs successful fallback recovery at `logging.INFO`.
- Returns the configured fallback value safely.

```python
from decorators import log_exceptions
from exceptions import DatabaseConnectionError

@log_exceptions(
    expected_exceptions=(DatabaseConnectionError,),
    default_return={"status": "offline_cached", "user": "guest"},
    user_message="User database connection failure"
)
def fetch_profile(user_id: int):
    # Risky operation that may fail
    raise DatabaseConnectionError("Replica offline")
```

### 3.4 Controlled Context Manager (`ErrorContext`)

Defined in `error_context.py`, this context manager implements `__enter__()` and `__exit__()`:
- Logs entry with context name at `INFO` level.
- Captures exceptions and logs full traceback with `logger.exception()`.
- Suppresses the exception *only* if it matches `handle_exceptions` and `suppress=True`.
- Returns `False` for unconfigured exceptions, allowing unexpected bugs to propagate naturally.

```python
from error_context import ErrorContext

with ErrorContext("Payment Gateway Verification", handle_exceptions=(KeyError, ValueError), suppress=True):
    # Only KeyError or ValueError will be intercepted and logged
    rates = {"USD": 1.0}
    _ = rates["EUR"]
```

---

## 4. The Eight Demonstration Scenarios

Implemented in `scenarios.py`:

1. **Arithmetic Test**:
   - Success: `50 / 5 = 10.0` logged at `INFO`.
   - Error: `50 / 0` triggers genuine `ZeroDivisionError`, logged at `ERROR` with traceback.
2. **File System Test**:
   - Success: Reads existing file logged at `INFO`.
   - Error: Missing file triggers genuine `FileNotFoundError`, logged at `ERROR` with traceback.
3. **Dictionary Lookup Test**:
   - Success: Retrieves existing key logged at `INFO`.
   - Error: Non-existent key triggers genuine `KeyError`, logged at `ERROR` with traceback.
4. **List Index Test**:
   - Success: Accesses valid element at index 1 logged at `INFO`.
   - Error: Index 99 triggers genuine `IndexError`, logged at `ERROR` with traceback.
5. **Value Conversion Test**:
   - Success: Converts string `"4096"` into integer logged at `INFO`.
   - Error: Converts string `"Invalid_Number"` triggering genuine `ValueError`, logged at `ERROR` with traceback.
6. **Type Mismatch Test**:
   - Success: Adds two integers `100 + 250` logged at `INFO`.
   - Error: Adds string and integer `"Port: " + 8080` triggering genuine `TypeError`, logged at `ERROR` with traceback.
7. **Decorator Test**:
   - Demonstrates `@log_exceptions` intercepting a simulated database failure, logging the traceback, and returning a safe fallback dictionary.
8. **Context Manager Test**:
   - Demonstrates `ErrorContext` capturing a `KeyError` within an operation block, recording the trace, and safely continuing application execution.

---

## 5. Installation & Execution Guide

### Prerequisites
- Python 3.8 or higher (compatible with Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14).
- Standard library only — no `pip install` required.

### Interactive Menu Mode
Run the application without flags to open the interactive CLI:

```bash
python3 main.py
```

Menu options:
- `1` : Run All 8 Demonstration Scenarios
- `2` : Run an Individual Scenario (Submenu 1 to 8)
- `3` : View Log File (`logs/app.log`)
- `4` : View Error Summary by Exception Type
- `5` : Run Automated Unit Tests
- `6` : Clear Log File (requires confirmation)
- `0` : Exit Application

### Command-Line Arguments
For scripted or automated execution:

```bash
python3 main.py --demo        # Run all 8 scenarios sequentially
python3 main.py --scenario 1  # Run individual scenario (1 to 8)
python3 main.py --summary     # Display error frequency breakdown
python3 main.py --view        # View latest log entries
python3 main.py --test        # Run automated unit test suite
python3 main.py --clear       # Prompt to clear logs
python3 main.py --clear --force  # Force clear logs without prompt
```

---

## 6. Automated Unit Tests

Automated testing is implemented using Python's standard `unittest` framework in `tests/test_scenarios.py`:

```bash
python3 -m unittest discover tests
# or
python3 main.py --test
```

### Test Coverage Summary:
- `test_log_file_created_automatically`: Verifies file and parent directory auto-creation.
- `test_reinitializing_logger_does_not_duplicate_messages`: Verifies handler deduplication.
- `test_successful_operations_do_not_generate_error_logs`: Confirms 0 ERROR entries on successes.
- `test_arithmetic_zero_division_records_traceback`: Validates arithmetic error logging.
- `test_file_not_found_records_traceback`: Validates filesystem error logging.
- `test_dictionary_key_error_records_traceback`: Validates dictionary error logging.
- `test_list_index_error_records_traceback`: Validates list index error logging.
- `test_value_error_records_traceback`: Validates type casting error logging.
- `test_type_error_records_traceback`: Validates type mismatch error logging.
- `test_decorator_returns_fallback_and_logs_recovery`: Validates decorator fallback behavior.
- `test_context_manager_suppresses_configured_exception`: Validates selective suppression.
- `test_context_manager_propagates_unconfigured_exception`: Confirms unhandled errors propagate.
- `test_clear_logs_functionality`: Validates log truncation.

**Result: 13 tests passed (0 failures, 0 errors in 0.007s).**

---

## 7. Real Execution Output

Below is an authentic terminal capture from running `python3 main.py --demo`:

```text
======================================================================
🚀 EXECUTING ALL 8 ERROR LOGGER DEMONSTRATION SCENARIOS
======================================================================

--- [Scenario 1] Arithmetic Test ---
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:38 (run_arithmetic_scenario) | Attempting arithmetic division operation: 50 / 5
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:41 (run_arithmetic_scenario) | Division operation successful: 50 / 5 = 10.0
[Success] Calculation Result: 50 / 5 = 10.0
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:38 (run_arithmetic_scenario) | Attempting arithmetic division operation: 50 / 0
[User Alert] Calculation Error: Division by zero is not permitted.
2026-10-13 22:24:02 | [ERROR   ] | scenarios.py:46 (run_arithmetic_scenario) | Failed arithmetic division: attempted division by zero (50 / 0)
Traceback (most recent call last):
  File "/Users/nandankumar/Nandan Prince/scenarios.py", line 40, in run_arithmetic_scenario
    result = a / b
             ~~^~~
ZeroDivisionError: division by zero

--- [Scenario 2] File System Test ---
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:60 (run_file_system_scenario) | Attempting to open and read file: 'scenarios.py'
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:64 (run_file_system_scenario) | File 'scenarios.py' read successfully (11330 characters read).
[Success] File read successfully: 'scenarios.py' (11330 chars)
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:60 (run_file_system_scenario) | Attempting to open and read file: 'missing_config_file.json'
[User Alert] File Error: The specified file could not be found.
2026-10-13 22:24:02 | [ERROR   ] | scenarios.py:69 (run_file_system_scenario) | Failed to open file: target path 'missing_config_file.json' does not exist on disk
Traceback (most recent call last):
  File "/Users/nandankumar/Nandan Prince/scenarios.py", line 62, in run_file_system_scenario
    with open(filepath, "r", encoding="utf-8") as f:
         ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'missing_config_file.json'

--- [Scenario 7] Decorator Test (@log_exceptions) ---
[Action] Executing function wrapped with @log_exceptions decorator...
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:178 (fetch_user_profile_decorated) | Calling decorated function 'fetch_user_profile_decorated' for user_id=-1
2026-10-13 22:24:02 | [ERROR   ] | decorators.py:44 (wrapper) | User database service connection failure - DatabaseConnectionError: Database replica cluster unreachable for user_id -1
Traceback (most recent call last):
  File "/Users/nandankumar/Nandan Prince/decorators.py", line 40, in wrapper
    return func(*args, **kwargs)
  File "/Users/nandankumar/Nandan Prince/scenarios.py", line 180, in fetch_user_profile_decorated
    raise DatabaseConnectionError(f"Database replica cluster unreachable for user_id {user_id}")
exceptions.DatabaseConnectionError: Database replica cluster unreachable for user_id -1
2026-10-13 22:24:02 | [INFO    ] | decorators.py:45 (wrapper) | Fallback recovery executed for 'fetch_user_profile_decorated': returning safe value [{'status': 'offline_cached', 'user': 'guest_profile'}].
[Success] Decorator recovered safely with fallback value: {'status': 'offline_cached', 'user': 'guest_profile'}

--- [Scenario 8] Context Manager Test (ErrorContext) ---
[Action] Entering ErrorContext protected block...
2026-10-13 22:24:02 | [INFO    ] | error_context.py:41 (__enter__) | Entering protected context: 'Payment Gateway Verification'
  - Inside context: querying exchange rate for missing currency 'GBP'...
2026-10-13 22:24:02 | [ERROR   ] | error_context.py:50 (__exit__) | Exception handled in context 'Payment Gateway Verification' - KeyError: 'GBP'
Traceback (most recent call last):
  File "/Users/nandankumar/Nandan Prince/scenarios.py", line 203, in run_context_manager_scenario
    _ = currency_rates["GBP"]  # Raises KeyError
        ~~~~~~~~~~~~~~^^^^^^^
KeyError: 'GBP'
2026-10-13 22:24:02 | [INFO    ] | error_context.py:59 (__exit__) | Safely suppressed KeyError in context 'Payment Gateway Verification'. Execution will continue.
[Success] Resumed execution safely after ErrorContext.

======================================================================
✅ All 8 Demonstration Scenarios Completed Successfully!
======================================================================
```

---

## 8. Sample `logs/app.log` Output

A representative snippet from the active `logs/app.log` file:

```text
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:38 (run_arithmetic_scenario) | Attempting arithmetic division operation: 50 / 0
2026-10-13 22:24:02 | [ERROR   ] | scenarios.py:46 (run_arithmetic_scenario) | Failed arithmetic division: attempted division by zero (50 / 0)
Traceback (most recent call last):
  File "/Users/nandankumar/Nandan Prince/scenarios.py", line 40, in run_arithmetic_scenario
    result = a / b
             ~~^~~
ZeroDivisionError: division by zero
2026-10-13 22:24:02 | [INFO    ] | scenarios.py:60 (run_file_system_scenario) | Attempting to open and read file: 'missing_config_file.json'
2026-10-13 22:24:02 | [ERROR   ] | scenarios.py:69 (run_file_system_scenario) | Failed to open file: target path 'missing_config_file.json' does not exist on disk
Traceback (most recent call last):
  File "/Users/nandankumar/Nandan Prince/scenarios.py", line 62, in run_file_system_scenario
    with open(filepath, "r", encoding="utf-8") as f:
         ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'missing_config_file.json'
```

---

## 9. Academic & Technical Defense Highlights

If presenting this project for evaluation or defense:
1. **Explain the Singleton Pattern in `ErrorLoggerManager`**: Ensures only one logger configuration exists, avoiding memory leaks and duplicate lines in log files.
2. **Explain `logger.exception()` vs `logger.error()`**: `logger.exception()` automatically captures `sys.exc_info()`, appending the stack trace without manually formatting traceback strings.
3. **Distinguish User Alert vs Log Entry**: User alerts are concise and non-technical for end users; log entries contain full technical diagnostics for developers.
4. **Demonstrate Decorator & Context Manager**: Show how `@log_exceptions` provides safe fallbacks for services and how `ErrorContext` selectively suppresses only configured exceptions while letting unexpected bugs bubble up.
