
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TestPilot Diagnostic Tools")


# --------------------------------------------------
# 1. PREDEFINED FAULTY FUNCTIONS
# Used only to reproduce the original bugs.
# --------------------------------------------------

def get_first_item(items):
    return items[0]


def divide_numbers(numerator, denominator):
    return numerator / denominator


# --------------------------------------------------
# 2. PREDEFINED CORRECTED FUNCTIONS
# These are safe, fixed examples used for regression
# testing. No user-provided code is executed.
# --------------------------------------------------

def fixed_get_first_item(items):
    if not items:
        return None
    return items[0]


def fixed_divide_numbers(numerator, denominator):
    if denominator == 0:
        raise ValueError("Denominator cannot be zero.")
    return numerator / denominator


# --------------------------------------------------
# 3. SOURCE INSPECTION TOOL
# --------------------------------------------------

@mcp.tool()
def inspect_synthetic_source(example_name: str) -> dict:
    """
    Inspect a supported synthetic debugging example.
    Does not execute arbitrary source code.
    """
    if example_name != "Empty List Bug":
        return {
            "success": False,
            "message": "Unsupported synthetic example.",
        }

    return {
        "success": True,
        "example_name": example_name,
        "function": "get_first_item",
        "operation": "return items[0]",
        "risk": (
            "The function accesses index 0 without checking "
            "whether the list contains an element."
        ),
        "safe_execution": True,
    }


# --------------------------------------------------
# 4. ORIGINAL BUG DIAGNOSTIC TOOLS
# These reproduce the faults for investigation.
# --------------------------------------------------

@mcp.tool()
def run_empty_list_diagnostic() -> dict:
    """Reproduce the empty-list bug and capture its exception."""
    test_input = []

    try:
        result = get_first_item(test_input)

        return {
            "success": True,
            "test_name": "empty_list_diagnostic",
            "input": test_input,
            "observed_exception": None,
            "observed_result": result,
            "diagnostic_confirmed": False,
            "details": (
                "The function returned without raising "
                "the expected IndexError."
            ),
        }

    except IndexError as error:
        return {
            "success": True,
            "test_name": "empty_list_diagnostic",
            "input": test_input,
            "observed_exception": type(error).__name__,
            "diagnostic_confirmed": True,
            "details": (
                "The predefined function raised an actual "
                "IndexError when called with an empty list."
            ),
        }

    except Exception as error:
        return {
            "success": False,
            "test_name": "empty_list_diagnostic",
            "input": test_input,
            "observed_exception": type(error).__name__,
            "diagnostic_confirmed": False,
            "details": (
                "An unexpected exception occurred. "
                "The expected diagnosis was not confirmed."
            ),
        }


@mcp.tool()
def run_division_by_zero_diagnostic() -> dict:
    """Reproduce the division-by-zero bug and capture its exception."""
    numerator = 10
    denominator = 0

    try:
        result = divide_numbers(numerator, denominator)

        return {
            "success": True,
            "test_name": "division_by_zero_diagnostic",
            "input": {
                "numerator": numerator,
                "denominator": denominator,
            },
            "observed_exception": None,
            "observed_result": result,
            "diagnostic_confirmed": False,
            "details": (
                "The function returned without raising "
                "the expected ZeroDivisionError."
            ),
        }

    except ZeroDivisionError as error:
        return {
            "success": True,
            "test_name": "division_by_zero_diagnostic",
            "input": {
                "numerator": numerator,
                "denominator": denominator,
            },
            "observed_exception": type(error).__name__,
            "diagnostic_confirmed": True,
            "details": (
                "The predefined function raised an actual "
                "ZeroDivisionError when dividing by zero."
            ),
        }

    except Exception as error:
        return {
            "success": False,
            "test_name": "division_by_zero_diagnostic",
            "input": {
                "numerator": numerator,
                "denominator": denominator,
            },
            "observed_exception": type(error).__name__,
            "diagnostic_confirmed": False,
            "details": (
                "An unexpected exception occurred. "
                "The expected diagnosis was not confirmed."
            ),
        }


# --------------------------------------------------
# 5. REGRESSION TEST HELPERS
# These helpers compare actual behaviour with expected
# behaviour for our predefined corrected functions.
# --------------------------------------------------

def _check_result(
    test_name: str,
    function,
    args: tuple,
    expected_result,
    expected_exception: str | None = None,
) -> dict:
    """Run one predefined test and record its outcome."""

    try:
        actual_result = function(*args)

        if expected_exception is not None:
            return {
                "name": test_name,
                "passed": False,
                "expected_result": expected_result,
                "actual_result": actual_result,
                "expected_exception": expected_exception,
                "observed_exception": None,
            }

        passed = actual_result == expected_result

        return {
            "name": test_name,
            "passed": passed,
            "expected_result": expected_result,
            "actual_result": actual_result,
            "expected_exception": None,
            "observed_exception": None,
        }

    except Exception as error:
        observed_exception = type(error).__name__

        passed = (
            expected_exception is not None
            and observed_exception == expected_exception
        )

        return {
            "name": test_name,
            "passed": passed,
            "expected_result": expected_result,
            "actual_result": None,
            "expected_exception": expected_exception,
            "observed_exception": observed_exception,
        }


# --------------------------------------------------
# 6. EMPTY-LIST REGRESSION TESTS
# --------------------------------------------------

@mcp.tool()
def run_empty_list_regression_tests() -> dict:
    """
    Test the predefined corrected list function with
    empty and non-empty lists.
    Does not execute arbitrary source code.
    """

    results = [
        _check_result(
            test_name="Empty list returns None",
            function=fixed_get_first_item,
            args=([],),
            expected_result=None,
        ),
        _check_result(
            test_name="Non-empty list returns first item",
            function=fixed_get_first_item,
            args=([10, 20, 30],),
            expected_result=10,
        ),
    ]

    regression_passed = all(
        result["passed"] for result in results
    )

    return {
        "success": True,
        "test_name": "empty_list_regression_tests",
        "regression_passed": regression_passed,
        "passed_count": sum(
            result["passed"] for result in results
        ),
        "total_count": len(results),
        "results": results,
        "safe_execution": True,
    }


# --------------------------------------------------
# 7. DIVISION REGRESSION TESTS
# --------------------------------------------------

@mcp.tool()
def run_division_regression_tests() -> dict:
    """
    Test the predefined corrected division function.
    A zero denominator must raise ValueError, while
    normal division must still work.
    Does not execute arbitrary source code.
    """

    results = [
        _check_result(
            test_name="Zero denominator is rejected",
            function=fixed_divide_numbers,
            args=(10, 0),
            expected_result=None,
            expected_exception="ValueError",
        ),
        _check_result(
            test_name="Normal division works",
            function=fixed_divide_numbers,
            args=(10, 2),
            expected_result=5.0,
        ),
    ]

    regression_passed = all(
        result["passed"] for result in results
    )

    return {
        "success": True,
        "test_name": "division_regression_tests",
        "regression_passed": regression_passed,
        "passed_count": sum(
            result["passed"] for result in results
        ),
        "total_count": len(results),
        "results": results,
        "safe_execution": True,
    }


# --------------------------------------------------
# 8. MCP SERVER ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
