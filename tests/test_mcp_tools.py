
import asyncio

from testpilot.mcp_client import call_mcp_tool


def test_mcp_can_inspect_supported_example():
    result = asyncio.run(
        call_mcp_tool(
            "inspect_synthetic_source",
            {"example_name": "Empty List Bug"},
        )
    )

    assert result["success"] is True
    assert result["function"] == "get_first_item"


def test_mcp_captures_actual_index_error():
    result = asyncio.run(
        call_mcp_tool("run_empty_list_diagnostic")
    )

    assert result["success"] is True
    assert result["observed_exception"] == "IndexError"
    assert result["diagnostic_confirmed"] is True


def test_mcp_diagnostic_uses_empty_list():
    result = asyncio.run(
        call_mcp_tool("run_empty_list_diagnostic")
    )

    assert result["input"] == []


def test_mcp_rejects_unknown_tool():
    try:
        asyncio.run(
            call_mcp_tool("run_arbitrary_code")
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Unknown tool should be rejected"
        )


def test_mcp_captures_actual_zero_division_error():
    result = asyncio.run(
        call_mcp_tool("run_division_by_zero_diagnostic")
    )

    assert result["success"] is True
    assert result["observed_exception"] == "ZeroDivisionError"
    assert result["diagnostic_confirmed"] is True


def test_division_diagnostic_uses_zero_denominator():
    result = asyncio.run(
        call_mcp_tool("run_division_by_zero_diagnostic")
    )

    assert result["input"]["numerator"] == 10
    assert result["input"]["denominator"] == 0


def test_mcp_client_allows_new_diagnostic_tool():
    result = asyncio.run(
        call_mcp_tool("run_division_by_zero_diagnostic")
    )

    assert result["test_name"] == "division_by_zero_diagnostic"


def test_empty_list_regression_tests_pass():
    result = asyncio.run(
        call_mcp_tool("run_empty_list_regression_tests")
    )

    assert result["success"] is True
    assert result["regression_passed"] is True
    assert result["passed_count"] == 2
    assert result["total_count"] == 2

    results = result["results"]
    assert all(test["passed"] for test in results)


def test_division_regression_tests_pass():
    result = asyncio.run(
        call_mcp_tool("run_division_regression_tests")
    )

    assert result["success"] is True
    assert result["regression_passed"] is True
    assert result["passed_count"] == 2
    assert result["total_count"] == 2

    results = result["results"]
    assert all(test["passed"] for test in results)


def test_regression_tools_are_allowlisted():
    empty_list_result = asyncio.run(
        call_mcp_tool("run_empty_list_regression_tests")
    )
    division_result = asyncio.run(
        call_mcp_tool("run_division_regression_tests")
    )

    assert empty_list_result["test_name"] == (
        "empty_list_regression_tests"
    )
    assert division_result["test_name"] == (
        "division_regression_tests"
    )
