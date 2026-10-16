
from testpilot.examples import EXAMPLES
from testpilot.workflow import build_workflow
from testpilot.workflow import regression_testing_agent

def make_initial_state(
    example_name="Empty List Bug",
    simulate_inconclusive=False,
):
    example = EXAMPLES[example_name]

    return {
        "example_name": example_name,
        "description": example["description"],
        "buggy_code": example["buggy_code"],
        "agent_trace": [],
        "retry_count": 0,
        "max_retries": 2,
        "simulate_inconclusive": simulate_inconclusive,
        "use_llm": False,
    }


def test_empty_list_investigation_produces_supported_diagnosis():
    workflow = build_workflow()
    result = workflow.invoke(make_initial_state())

    assert result["failure_type"] == "Indexing error"
    assert result["test_passed"] is True
    assert result["validation_status"] == (
        "Diagnosis supported by observed MCP evidence"
    )
    assert result["needs_human_review"] is False
    assert len(result["agent_trace"]) == 6


def test_division_by_zero_investigation_produces_supported_diagnosis():
    workflow = build_workflow()
    result = workflow.invoke(
        make_initial_state(example_name="Division by Zero")
    )

    assert result["example_name"] == "Division by Zero"
    assert result["failure_type"] == "Division by zero"
    assert result["test_passed"] is True
    assert result["mcp_used"] is True
    assert result["mcp_result"]["observed_exception"] == "ZeroDivisionError"
    assert result["mcp_result"]["diagnostic_confirmed"] is True
    assert result["validation_status"] == (
        "Diagnosis supported by observed MCP evidence"
    )
    assert result["needs_human_review"] is False
    assert len(result["agent_trace"]) == 6


def test_inconclusive_evidence_escalates_after_configured_attempts():
    result = build_workflow().invoke(
        make_initial_state(simulate_inconclusive=True)
    )

    # The investigation must not claim a confirmed diagnosis.
    assert result["test_passed"] is False
    assert result["mcp_used"] is False
    assert result["mcp_result"] == {}

    # The workflow should stop after the configured limit.
    assert result["retry_count"] == 2
    assert result["needs_human_review"] is True
    assert result["validation_status"] == (
        "Evidence insufficient; human review required"
    )

    # The report should explain that further investigation is needed.
    assert "Human investigation is required" in (
        result["final_report"]
    )


def test_regression_agent_blocks_execution_without_approval():
    state = {
        "example_name": "Empty List Bug",
        "validation_status": (
            "Diagnosis supported by observed MCP evidence"
        ),
        "test_passed": True,
        "needs_human_review": False,
        "fix_available": True,
        "fix_approved": False,
        "agent_trace": [],
    }

    result = regression_testing_agent(state)

    assert result["regression_passed"] is False
    assert result["regression_results"] == []
    assert "human approval" in result["regression_summary"].lower()
    assert any(
        "Blocked" in entry for entry in result["agent_trace"]
    )


def test_regression_agent_blocks_execution_without_a_fix():
    state = {
        "example_name": "Empty List Bug",
        "validation_status": (
            "Diagnosis supported by observed MCP evidence"
        ),
        "test_passed": True,
        "needs_human_review": False,
        "fix_available": False,
        "fix_approved": True,
        "agent_trace": [],
    }

    result = regression_testing_agent(state)

    assert result["regression_passed"] is False
    assert result["regression_results"] == []
    assert "no fix is available" in result["regression_summary"].lower()
    assert any(
        "Blocked" in entry for entry in result["agent_trace"]
    )


def test_regression_agent_runs_tests_after_approval():
    state = {
        "example_name": "Empty List Bug",
        "validation_status": (
            "Diagnosis supported by observed MCP evidence"
        ),
        "test_passed": True,
        "needs_human_review": False,
        "fix_available": True,
        "fix_approved": True,
        "agent_trace": [],
    }

    result = regression_testing_agent(state)

    assert result["regression_passed"] is True
    assert len(result["regression_results"]) == 2
    assert all(
        test.get("passed", False)
        for test in result["regression_results"]
    )
    assert "2/2" in result["regression_summary"]
    assert any(
        "Regression Testing Agent" in entry
        for entry in result["agent_trace"]
    )
