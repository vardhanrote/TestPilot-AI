import asyncio

from langgraph.graph import END, START, StateGraph
from testpilot.examples import EXAMPLES
from testpilot.llm import generate_root_cause
from testpilot.mcp_client import call_mcp_tool
from testpilot.state import InvestigationState


# Agent 1: Triage Agent
def triage_agent(state: InvestigationState) -> dict:
    """Classify the failure and set its priority."""

    code = state.get("buggy_code", "")
    example_name = state.get("example_name", "Empty List Bug")

    if example_name == "Division by Zero" or "/" in code:
        failure_type = "Division by zero"
        priority = "High"
    elif "items[0]" in code:
        failure_type = "Indexing error"
        priority = "High"
    else:
        failure_type = "Unknown failure"
        priority = "Medium"

    return {
        "failure_type": failure_type,
        "priority": priority,
        "agent_trace": [
            *state.get("agent_trace", []),
            f"Triage Agent: classified as {failure_type}.",
        ],
    }


# Agent 2: Root-Cause Agent
def root_cause_agent(state: InvestigationState) -> dict:
    """Use Ollama when enabled; otherwise use rule-based analysis."""

    code = state.get("buggy_code", "")
    description = state.get("description", "")
    example_name = state.get("example_name", "Empty List Bug")
    attempt = state.get("retry_count", 0) + 1
    agent_trace = list(state.get("agent_trace", []))

    # Rule-based fallback
    if example_name == "Division by Zero":
        fallback_hypothesis = (
            "The function attempts to divide by zero "
            "without checking whether the denominator is zero."
        )
    elif "items[0]" in code:
        fallback_hypothesis = (
            "The function accesses index 0 without checking "
            "whether the list contains any elements."
        )
    else:
        fallback_hypothesis = (
            "The root cause is uncertain; more evidence is needed."
        )

    hypothesis = fallback_hypothesis
    agent_method = "rule-based"

    # Use Ollama when enabled
    if state.get("use_llm", False):
        try:
            hypothesis = generate_root_cause(
                example_name=example_name,
                description=description,
                buggy_code=code,
            )

            if not hypothesis or not hypothesis.strip():
                raise ValueError(
                    "The model returned an empty response."
                )

            agent_method = "Ollama LLM"

        except Exception as error:
            # Fall back to rule-based analysis if Ollama fails.
            hypothesis = fallback_hypothesis
            agent_method = "rule-based fallback"

            agent_trace.append(
                "Root-Cause Agent: Ollama unavailable; "
                "used rule-based fallback "
                f"({type(error).__name__})."
            )

    agent_trace.append(
        f"Root-Cause Agent: {agent_method} analysis "
        f"on attempt {attempt}."
    )

    return {
        "hypothesis": hypothesis,
        "agent_trace": agent_trace,
    }


# Agent 3: Test Selection Agent
def test_selection_agent(state: InvestigationState) -> dict:
    """Choose a diagnostic test based on the selected example."""

    example_name = state.get("example_name", "Empty List Bug")

    if example_name == "Division by Zero":
        selected_test = (
            "Call divide_numbers(10, 0) and check whether "
            "the function raises ZeroDivisionError."
        )
    else:
        selected_test = (
            "Call get_first_item([]) and check whether "
            "the function raises IndexError."
        )

    if state.get("retry_count", 0) > 0:
        selected_test = (
            "Retry: " + selected_test
            + " Check whether the observed exception supports "
            "the current hypothesis."
        )

    return {
        "selected_test": selected_test,
        "agent_trace": [
            *state.get("agent_trace", []),
            "Test Selection Agent: selected a diagnostic test.",
        ],
    }


# Agent 4: Experiment Agent
def experiment_agent(state: InvestigationState) -> dict:
    """Run the selected controlled diagnostic through MCP."""

    agent_trace = list(state.get("agent_trace", []))

    if state.get("simulate_inconclusive", False):
        agent_trace.append(
            "Experiment Agent: simulated inconclusive result; "
            "MCP diagnostic was not called."
        )

        return {
            "test_output": (
                "Diagnostic result inconclusive. "
                "No reliable evidence was obtained."
            ),
            "test_passed": False,
            "mcp_result": {},
            "mcp_used": False,
            "agent_trace": agent_trace,
        }

    example_name = state.get(
        "example_name",
        "Empty List Bug",
    )

    diagnostic_tools = {
        "Empty List Bug": "run_empty_list_diagnostic",
        "Division by Zero": "run_division_by_zero_diagnostic",
    }

    tool_name = diagnostic_tools.get(example_name)

    if tool_name is None:
        agent_trace.append(
            "Experiment Agent: unsupported example; "
            "no diagnostic tool was called."
        )

        return {
            "test_output": (
                f"No diagnostic tool is configured for "
                f"'{example_name}'."
            ),
            "test_passed": False,
            "mcp_result": {},
            "mcp_used": False,
            "agent_trace": agent_trace,
        }

    try:
        result = asyncio.run(
            call_mcp_tool(tool_name)
        )

        expected_exceptions = {
            "Empty List Bug": "IndexError",
            "Division by Zero": "ZeroDivisionError",
        }

        expected_exception = expected_exceptions[example_name]

        diagnostic_confirmed = (
            result.get("success") is True
            and result.get("diagnostic_confirmed") is True
            and result.get("observed_exception")
            == expected_exception
        )

        observed_exception = result.get(
            "observed_exception",
            "Unknown",
        )

        test_output = (
            f"MCP diagnostic result: {observed_exception}. "
            f"Details: {result.get('details', 'No details returned.')}"
        )

        agent_trace.append(
            f"Experiment Agent: invoked MCP tool '{tool_name}'."
        )

        return {
            "test_output": test_output,
            "test_passed": diagnostic_confirmed,
            "mcp_result": result,
            "mcp_used": True,
            "agent_trace": agent_trace,
        }

    except Exception as error:
        agent_trace.append(
            "Experiment Agent: MCP diagnostic call failed "
            f"({type(error).__name__})."
        )

        return {
            "test_output": (
                "MCP diagnostic failed. The result cannot "
                "be treated as confirmed evidence."
            ),
            "test_passed": False,
            "mcp_result": {},
            "mcp_used": False,
            "agent_trace": agent_trace,
        }


# Agent 5: Validation Agent
def validation_agent(state: InvestigationState) -> dict:
    """Validate the hypothesis against the diagnostic evidence."""

    agent_trace = list(state.get("agent_trace", []))

    result = state.get("mcp_result", {})
    hypothesis = state.get("hypothesis", "")
    test_confirmed = state.get("test_passed", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    example_name = state.get("example_name", "Empty List Bug")

    expected_evidence = {
        "Empty List Bug": {
            "exception": "IndexError",
            "hypothesis_terms": ("index 0", "empty list"),
        },
        "Division by Zero": {
            "exception": "ZeroDivisionError",
            "hypothesis_terms": ("zero", "denominator"),
        },
    }

    scenario = expected_evidence.get(example_name)

    evidence_valid = (
        scenario is not None
        and state.get("mcp_used", False)
        and result.get("success") is True
        and result.get("diagnostic_confirmed") is True
        and result.get("observed_exception")
        == scenario["exception"]
        and test_confirmed is True
        and any(
            term in hypothesis.lower()
            for term in scenario["hypothesis_terms"]
        )
    )

    if evidence_valid:
        validation_status = (
            "Diagnosis supported by observed MCP evidence"
        )
        needs_human_review = False

        final_report = (
            f"The diagnostic tool executed the predefined synthetic "
            f"function for '{example_name}' and captured the actual "
            f"exception '{result.get('observed_exception')}'. "
            f"The root-cause hypothesis is consistent with the "
            f"observed evidence. Arbitrary source code was not "
            f"executed, and no code fix was applied."
        )

        next_action = (
            "Review the proposed fix under human supervision "
            "and run regression tests."
        )

    else:
        retry_count += 1
        needs_human_review = retry_count >= max_retries

        if needs_human_review:
            validation_status = (
                "Evidence insufficient; human review required"
            )
            final_report = (
                "The diagnosis could not be validated against the "
                "expected MCP evidence. Human investigation is required."
            )
            next_action = (
                "Inspect the MCP result and diagnostic configuration "
                "before making code changes."
            )
        else:
            validation_status = (
                "Evidence insufficient; retry required"
            )
            final_report = (
                "The current diagnostic did not provide sufficient "
                "evidence to confirm the root-cause hypothesis."
            )
            next_action = (
                "Retry the investigation and collect diagnostic evidence."
            )

    agent_trace.append(
        f"Validation Agent: {validation_status}."
    )

    return {
        "validation_status": validation_status,
        "needs_human_review": needs_human_review,
        "retry_count": retry_count,
        "max_retries": max_retries,
        "final_report": final_report,
        "next_action": next_action,
        "agent_trace": agent_trace,
    }


def fix_recommendation_agent(state: InvestigationState) -> InvestigationState:
    """Recommend a predefined fix only after the diagnosis is validated."""

    trace = list(state.get("agent_trace", []))

    diagnosis_validated = (
        state.get("validation_status")
        == "Diagnosis supported by observed MCP evidence"
        and state.get("test_passed", False)
        and not state.get("needs_human_review", False)
    )

    if not diagnosis_validated:
        trace.append(
            "Fix Recommendation Agent: Fix withheld because the diagnosis "
            "is not sufficiently validated."
        )

        return {
            "proposed_fix": "",
            "fix_available": False,
            "fix_approved": False,
            "agent_trace": trace,
            "next_action": (
                "Review the investigation evidence before considering a fix."
            ),
        }

    example_name = state.get("example_name", "")

    example = EXAMPLES.get(example_name)

    if not example or not example.get("proposed_fix"):
        trace.append(
            "Fix Recommendation Agent: No predefined fix is available."
        )

        return {
            "proposed_fix": "",
            "fix_available": False,
            "fix_approved": False,
            "agent_trace": trace,
            "next_action": (
                "A human should review the failure and prepare a correction."
            ),
        }

    proposed_fix = example["proposed_fix"]

    trace.append(
        "Fix Recommendation Agent: Generated a predefined fix recommendation. "
        "No source code was modified."
    )

    return {
        "proposed_fix": proposed_fix,
        "fix_available": True,
        "fix_approved": False,
        "agent_trace": trace,
        "next_action": (
            "Review the proposed fix. Human approval is required before "
            "the regression-testing stage can run."
        ),
    }


def regression_testing_agent(
    state: InvestigationState,
) -> InvestigationState:
    """Run predefined MCP regression tests only after human approval."""

    trace = list(state.get("agent_trace", []))

    if state.get("fix_approved") is not True:
        trace.append(
            "Regression Testing Agent: Blocked because human approval "
            "has not been granted."
        )

        return {
            "regression_results": [],
            "regression_passed": False,
            "regression_summary": (
                "Regression tests were not run because human approval "
                "is required."
            ),
            "agent_trace": trace,
        }

    if not state.get("fix_available", False):
        trace.append(
            "Regression Testing Agent: Blocked because no fix is available."
        )

        return {
            "regression_results": [],
            "regression_passed": False,
            "regression_summary": (
                "Regression tests were not run because no fix is available."
            ),
            "agent_trace": trace,
        }

    if (
        state.get("validation_status")
        != "Diagnosis supported by observed MCP evidence"
        or state.get("needs_human_review", False)
    ):
        trace.append(
            "Regression Testing Agent: Blocked because the diagnosis "
            "has not been validated."
        )

        return {
            "regression_results": [],
            "regression_passed": False,
            "regression_summary": (
                "Regression tests were blocked because the diagnosis "
                "requires further review."
            ),
            "agent_trace": trace,
        }

    example_name = state.get("example_name", "")

    if example_name == "Empty List Bug":
        tool_name = "run_empty_list_regression_tests"
    elif example_name == "Division by Zero":
        tool_name = "run_division_regression_tests"
    else:
        trace.append(
            "Regression Testing Agent: No regression tool is configured "
            "for this scenario."
        )

        return {
            "regression_results": [],
            "regression_passed": False,
            "regression_summary": (
                f"No predefined regression tests exist for {example_name}."
            ),
            "agent_trace": trace,
        }

    try:
        result = asyncio.run(call_mcp_tool(tool_name))

        regression_results = result.get("results", [])
        regression_passed = result.get("regression_passed", False)

        passed_count = sum(
            1 for test in regression_results if test.get("passed", False)
        )
        total_count = len(regression_results)

        if regression_passed:
            summary = (
                f"All {passed_count}/{total_count} regression tests passed."
            )
        else:
            summary = (
                f"{passed_count}/{total_count} regression tests passed. "
                "Review the failed tests before proceeding."
            )

        trace.append(
            f"Regression Testing Agent: Executed {tool_name}; "
            f"{passed_count}/{total_count} tests passed."
        )

        return {
            "regression_results": regression_results,
            "regression_passed": regression_passed,
            "regression_summary": summary,
            "agent_trace": trace,
        }

    except Exception as error:
        trace.append(
            "Regression Testing Agent: MCP regression testing failed."
        )

        return {
            "regression_results": [],
            "regression_passed": False,
            "regression_summary": (
                f"Regression testing could not complete: "
                f"{type(error).__name__}: {error}"
            ),
            "agent_trace": trace,
        }


def build_final_investigation_report(
    state: InvestigationState,
) -> str:
    """Build a consolidated report from the latest investigation state."""

    example_name = state.get("example_name", "Unknown scenario")
    failure_type = state.get("failure_type", "Unknown failure")
    priority = state.get("priority", "Not assigned")
    hypothesis = state.get(
        "hypothesis",
        "No root-cause hypothesis was generated.",
    )
    selected_test = state.get(
        "selected_test",
        "No diagnostic test was selected.",
    )
    test_output = state.get(
        "test_output",
        "No diagnostic output is available.",
    )
    validation_status = state.get(
        "validation_status",
        "Not validated",
    )
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    needs_human_review = state.get("needs_human_review", False)

    mcp_result = state.get("mcp_result", {})
    observed_exception = mcp_result.get(
        "observed_exception",
        "Not confirmed",
    )

    proposed_fix = state.get("proposed_fix", "")
    fix_available = state.get("fix_available", False)
    fix_approved = state.get("fix_approved", False)

    regression_results = state.get("regression_results", [])
    regression_passed = state.get("regression_passed", False)
    regression_summary = state.get(
        "regression_summary",
        "Regression tests have not been run.",
    )

    if fix_available and proposed_fix:
        fix_section = (
            "RECOMMENDED FIX\n"
            f"{proposed_fix}\n\n"
            "Status: Recommendation only. The original source code "
            "has not been modified."
        )
    else:
        fix_section = (
            "RECOMMENDED FIX\n"
            "No fix recommendation is available. Human review may "
            "be required before proposing a correction."
        )

    if regression_results:
        regression_status = (
            "Passed"
            if regression_passed
            else "Failed or incomplete"
        )

        regression_lines = [
            f"- {item.get('name', item.get('test_name', 'Regression test'))}: "
            f"{'PASSED' if item.get('passed', False) else 'FAILED'}"
            for item in regression_results
        ]

        regression_section = (
            f"Status: {regression_status}\n"
            f"Summary: {regression_summary}\n"
            f"Human approval recorded: {'Yes' if fix_approved else 'No'}\n"
            + "\n".join(regression_lines)
            + "\n\nThese results apply to the predefined regression "
            "functions, not to an automatically patched original file."
        )
    else:
        regression_section = (
            "Status: Not run\n"
            f"Details: {regression_summary}\n"
            f"Human approval recorded: {'Yes' if fix_approved else 'No'}"
        )

    human_review_status = (
        "Required"
        if needs_human_review
        else "Not currently required by the validation workflow"
    )

    next_action = state.get(
        "next_action",
        "Review the investigation results.",
    )

    return (
        "TESTPILOT AI — FINAL INVESTIGATION REPORT\n"
        "==========================================\n\n"
        "1. FAILURE SUMMARY\n"
        f"Scenario: {example_name}\n"
        f"Failure type: {failure_type}\n"
        f"Priority: {priority}\n\n"
        "2. ROOT-CAUSE HYPOTHESIS\n"
        f"{hypothesis}\n\n"
        "3. DIAGNOSTIC EVIDENCE\n"
        f"Selected test: {selected_test}\n"
        f"Observed output: {test_output}\n"
        f"Observed exception: {observed_exception}\n"
        f"MCP diagnostic used: "
        f"{'Yes' if state.get('mcp_used', False) else 'No'}\n"
        f"Diagnostic confirmed: "
        f"{'Yes' if state.get('test_passed', False) else 'No'}\n\n"
        "4. VALIDATION\n"
        f"Status: {validation_status}\n"
        f"Retries used: {retry_count}/{max_retries}\n"
        f"Human review required: {human_review_status}\n\n"
        f"5. {fix_section}\n\n"
        "6. REGRESSION TESTING\n"
        f"{regression_section}\n\n"
        "7. NEXT ACTION\n"
        f"{next_action}\n\n"
        "SAFETY NOTE\n"
        "TestPilot AI uses predefined diagnostic and regression tools. "
        "It does not execute arbitrary uploaded source code or "
        "automatically apply patches to the original source."
    )


# Conditional router

# Conditional router
def route_after_validation(state: InvestigationState) -> str:
    """Choose whether to retry, recommend a fix, or finish."""

    if state.get("needs_human_review", False):
        return "finish"

    if (
        state.get("validation_status")
        == "Diagnosis supported by observed MCP evidence"
        and state.get("test_passed", False)
    ):
        return "recommend_fix"

    if state.get("retry_count", 0) < state.get("max_retries", 2):
        return "retry"

    return "finish"

    """Choose whether to retry, recommend a fix, or finish."""

    if state.get("needs_human_review", False):
        return "finish"

    if (
        state.get("validation_status")
        == "Diagnosis supported by observed MCP evidence"
        and state.get("test_passed", False)
    ):
        return "recommend_fix"

    if state.get("retry_count", 0) < state.get("max_retries", 2):
        return "retry"

    return "finish"
    """Choose whether to finish or repeat the investigation."""

    if state.get("needs_human_review", False):
        return "finish"

    if state.get("test_passed", False):
        return "finish"

    if state.get("retry_count", 0) < state.get("max_retries", 2):
        return "retry"

    return "finish"



def build_workflow():
    """Build the investigation and fix-recommendation workflow."""

    graph = StateGraph(InvestigationState)

    graph.add_node("triage", triage_agent)
    graph.add_node("root_cause", root_cause_agent)
    graph.add_node("test_selection", test_selection_agent)
    graph.add_node("experiment", experiment_agent)
    graph.add_node("validation", validation_agent)
    graph.add_node("fix_recommendation", fix_recommendation_agent)

    graph.add_edge(START, "triage")
    graph.add_edge("triage", "root_cause")
    graph.add_edge("root_cause", "test_selection")
    graph.add_edge("test_selection", "experiment")
    graph.add_edge("experiment", "validation")

    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "retry": "root_cause",
            "recommend_fix": "fix_recommendation",
            "finish": END,
        },
    )

    graph.add_edge("fix_recommendation", END)

    return graph.compile()

    """Build the investigation and fix-recommendation workflow."""

    graph = StateGraph(InvestigationState)

    graph.add_node("triage", triage_agent)
    graph.add_node("root_cause", root_cause_agent)
    graph.add_node("test_selection", test_selection_agent)
    graph.add_node("experiment", experiment_agent)
    graph.add_node("validation", validation_agent)
    graph.add_node("fix_recommendation", fix_recommendation_agent)

    graph.add_edge(START, "triage")
    graph.add_edge("triage", "root_cause")
    graph.add_edge("root_cause", "test_selection")
    graph.add_edge("test_selection", "experiment")
    graph.add_edge("experiment", "validation")

    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "retry": "root_cause",
            "recommend_fix": "fix_recommendation",
            "finish": END,
        },
    )

    graph.add_edge("fix_recommendation", END)

    return graph.compile()
    