"""
Error Scenarios and Demonstration Handlers
==========================================
Implements eight real-world scenarios demonstrating genuine Python exception
handling, real-time logging, user-friendly alerts, and recovery mechanisms.

Scenarios:
1. Arithmetic Test (Success + ZeroDivisionError)
2. File System Test (Success + FileNotFoundError)
3. Dictionary Lookup Test (Success + KeyError)
4. List Index Test (Success + IndexError)
5. Value Conversion Test (Success + ValueError)
6. Type Mismatch Test (Success + TypeError)
7. Decorator Test (@log_exceptions fallback recovery)
8. Context Manager Test (ErrorContext suppression)
"""

import os
from typing import Any, Dict, List, Optional

from error_logger import get_logger
from decorators import log_exceptions
from error_context import ErrorContext
from exceptions import DatabaseConnectionError

logger = get_logger()


# =========================================================================
# 1. Arithmetic Test (ZeroDivisionError)
# =========================================================================
def run_arithmetic_scenario(a: float, b: float) -> Optional[float]:
    """
    Executes arithmetic division.
    Logs successful division at INFO level.
    Catches ZeroDivisionError, displays user alert, and logs full traceback at ERROR level.
    """
    logger.info("Attempting arithmetic division operation: %s / %s", a, b)
    try:
        result = a / b
        logger.info("Division operation successful: %s / %s = %s", a, b, result)
        print(f"[Success] Calculation Result: {a} / {b} = {result}")
        return result
    except ZeroDivisionError:
        print("[User Alert] Calculation Error: Division by zero is not permitted.")
        logger.exception("Failed arithmetic division: attempted division by zero (%s / %s)", a, b)
        return None


# =========================================================================
# 2. File System Test (FileNotFoundError)
# =========================================================================
def run_file_system_scenario(filepath: str) -> Optional[str]:
    """
    Attempts to read a file from disk.
    Logs successful read at INFO level.
    Catches FileNotFoundError, displays user alert, and logs full traceback at ERROR level.
    """
    safe_name = os.path.basename(filepath)
    logger.info("Attempting to open and read file: '%s'", safe_name)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info("File '%s' read successfully (%d characters read).", safe_name, len(content))
        print(f"[Success] File read successfully: '{safe_name}' ({len(content)} chars)")
        return content
    except FileNotFoundError:
        print("[User Alert] File Error: The specified file could not be found.")
        logger.exception("Failed to open file: target path '%s' does not exist on disk", safe_name)
        return None


# =========================================================================
# 3. Dictionary Lookup Test (KeyError)
# =========================================================================
def run_dictionary_lookup_scenario(data: Dict[str, Any], key: str) -> Any:
    """
    Retrieves a value from a dictionary by key.
    Logs successful lookup at INFO level.
    Catches KeyError, displays user alert, and logs full traceback at ERROR level.
    """
    logger.info("Attempting dictionary lookup for key: '%s'", key)
    try:
        value = data[key]
        logger.info("Dictionary lookup succeeded for key '%s': value retrieved.", key)
        print(f"[Success] Retrieved key '{key}' -> {value}")
        return value
    except KeyError:
        print("[User Alert] Data Error: The requested dictionary key was not found.")
        logger.exception("KeyError encountered: requested key '%s' not present in dictionary", key)
        return None


# =========================================================================
# 4. List Index Test (IndexError)
# =========================================================================
def run_list_index_scenario(items: List[Any], index: int) -> Any:
    """
    Accesses an element at a given index from a list.
    Logs successful access at INFO level.
    Catches IndexError, displays user alert, and logs full traceback at ERROR level.
    """
    logger.info("Attempting list index access at position %d (list length: %d)", index, len(items))
    try:
        item = items[index]
        logger.info("List item retrieved successfully at index %d: %s", index, item)
        print(f"[Success] Element at index {index} -> {item}")
        return item
    except IndexError:
        print("[User Alert] Index Error: The requested list position is out of bounds.")
        logger.exception("IndexError encountered: index %d is out of range for list size %d", index, len(items))
        return None


# =========================================================================
# 5. Value Conversion Test (ValueError)
# =========================================================================
def run_value_conversion_scenario(raw_input: str) -> Optional[int]:
    """
    Parses a string into an integer.
    Logs successful conversion at INFO level.
    Catches ValueError, displays user alert, and logs full traceback at ERROR level.
    """
    logger.info("Attempting integer conversion on input: '%s'", raw_input)
    try:
        parsed_val = int(raw_input)
        logger.info("Value conversion successful: parsed integer %d", parsed_val)
        print(f"[Success] Converted integer: {parsed_val}")
        return parsed_val
    except ValueError:
        print("[User Alert] Input Error: The supplied value cannot be converted to an integer.")
        logger.exception("ValueError encountered: string '%s' is not a valid integer literal", raw_input)
        return None


# =========================================================================
# 6. Type Mismatch Test (TypeError)
# =========================================================================
def run_type_mismatch_scenario(a: Any, b: Any) -> Any:
    """
    Performs addition on two operands.
    Logs successful operation at INFO level.
    Catches TypeError, displays user alert, and logs full traceback at ERROR level.
    """
    logger.info(
        "Attempting addition between type '%s' and '%s'",
        type(a).__name__,
        type(b).__name__,
    )
    try:
        result = a + b
        logger.info("Addition operation succeeded: result = %s", result)
        print(f"[Success] Addition Result: {result}")
        return result
    except TypeError:
        print("[User Alert] Type Error: The supplied data types cannot be used in this operation.")
        logger.exception(
            "TypeError encountered: unsupported operand types for +: '%s' and '%s'",
            type(a).__name__,
            type(b).__name__,
        )
        return None


# =========================================================================
# 7. Decorator Test (@log_exceptions)
# =========================================================================
@log_exceptions(
    expected_exceptions=(DatabaseConnectionError,),
    default_return={"status": "offline_cached", "user": "guest_profile"},
    user_message="User database service connection failure",
)
def fetch_user_profile_decorated(user_id: int) -> Dict[str, Any]:
    """
    Protected function wrapped with @log_exceptions decorator.
    Simulates database query failure and recovers using configured fallback.
    """
    logger.info("Calling decorated function 'fetch_user_profile_decorated' for user_id=%d", user_id)
    if user_id <= 0:
        raise DatabaseConnectionError(f"Database replica cluster unreachable for user_id {user_id}")
    return {"status": "active", "user": f"user_{user_id}"}


def run_decorator_scenario() -> Dict[str, Any]:
    """Demonstrates successful fallback recovery using the @log_exceptions decorator."""
    print("[Action] Executing function wrapped with @log_exceptions decorator...")
    result = fetch_user_profile_decorated(-1)
    print(f"[Success] Decorator recovered safely with fallback value: {result}")
    return result


# =========================================================================
# 8. Context Manager Test (ErrorContext)
# =========================================================================
def run_context_manager_scenario() -> bool:
    """
    Demonstrates controlled exception suppression and error logging using ErrorContext.
    """
    print("[Action] Entering ErrorContext protected block...")
    with ErrorContext("Payment Gateway Verification", handle_exceptions=(KeyError, ValueError), suppress=True):
        currency_rates = {"USD": 1.0, "EUR": 0.92}
        print("  - Inside context: querying exchange rate for missing currency 'GBP'...")
        _ = currency_rates["GBP"]  # Raises KeyError
        print("  - This line will not execute.")

    print("[Success] Resumed execution safely after ErrorContext.")
    return True


# =========================================================================
# Comprehensive Demonstration Runner
# =========================================================================
def run_all_scenarios() -> None:
    """Executes all eight scenarios sequentially, showcasing successes and errors."""
    print("=" * 70)
    print("🚀 EXECUTING ALL 8 ERROR LOGGER DEMONSTRATION SCENARIOS")
    print("=" * 70)

    # 1. Arithmetic Test
    print("\n--- [Scenario 1] Arithmetic Test ---")
    run_arithmetic_scenario(50, 5)   # Success
    run_arithmetic_scenario(50, 0)   # Error (ZeroDivisionError)

    # 2. File System Test
    print("\n--- [Scenario 2] File System Test ---")
    # Read self as success
    run_file_system_scenario(__file__)
    # Read missing file as error
    run_file_system_scenario("missing_config_file.json")

    # 3. Dictionary Lookup Test
    print("\n--- [Scenario 3] Dictionary Lookup Test ---")
    sample_dict = {"server_host": "127.0.0.1", "server_port": 8080}
    run_dictionary_lookup_scenario(sample_dict, "server_port")     # Success
    run_dictionary_lookup_scenario(sample_dict, "database_token")  # Error (KeyError)

    # 4. List Index Test
    print("\n--- [Scenario 4] List Index Test ---")
    sample_list = ["System Core", "Network Manager", "Logger Service"]
    run_list_index_scenario(sample_list, 1)   # Success
    run_list_index_scenario(sample_list, 99)  # Error (IndexError)

    # 5. Value Conversion Test
    print("\n--- [Scenario 5] Value Conversion Test ---")
    run_value_conversion_scenario("4096")             # Success
    run_value_conversion_scenario("Invalid_Number")   # Error (ValueError)

    # 6. Type Mismatch Test
    print("\n--- [Scenario 6] Type Mismatch Test ---")
    run_type_mismatch_scenario(100, 250)              # Success
    run_type_mismatch_scenario("Connection Port: ", 8080)  # Error (TypeError)

    # 7. Decorator Test
    print("\n--- [Scenario 7] Decorator Test (@log_exceptions) ---")
    run_decorator_scenario()

    # 8. Context Manager Test
    print("\n--- [Scenario 8] Context Manager Test (ErrorContext) ---")
    run_context_manager_scenario()

    print("\n" + "=" * 70)
    print("✅ All 8 Demonstration Scenarios Completed Successfully!")
    print("=" * 70)
