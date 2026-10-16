import hashlib
import streamlit as st

from testpilot.examples import EXAMPLES
from testpilot.workflow import (
    build_workflow,
    build_final_investigation_report,
    regression_testing_agent,
)


st.set_page_config(
    page_title="TestPilot AI",
    page_icon="🧪",
    layout="wide",
)

st.title("TestPilot AI")
st.subheader(
    "Agentic AI for Automated Test Failure Investigation"
)

st.write(
    "Investigate software test failures using specialized agents, "
    "controlled experiments, conditional routing, and validation."
)

st.info(
    "Current version: rule-based agents with LangGraph orchestration "
    "and MCP-powered diagnostic tools. Optional local Ollama "
    "integration is available for root-cause analysis."
)

st.divider()

st.markdown("## Select a debugging scenario")

example_name = st.selectbox(
    "Synthetic test failure",
    options=list(EXAMPLES.keys()),
)

example = EXAMPLES[example_name]

left, right = st.columns(2)

with left:
    st.markdown("### Problem description")
    st.write(example["description"])

    st.markdown("### Faulty code")
    st.code(example["buggy_code"], language="python")

with right:
    st.markdown("### Test input")
    st.code(example["input_description"], language="python")

    st.markdown("### Expected exception")
    st.write(example["expected_exception"])

st.divider()

st.markdown("## Investigation settings")

simulate_inconclusive = st.checkbox(
    "Simulate inconclusive evidence",
    value=False,
    help=(
        "Demonstration only: forces the diagnostic experiment "
        "to return inconclusive evidence so you can observe "
        "the retry and human-escalation workflow."
    ),
)

max_retries = st.slider(
    "Maximum investigation attempts",
    min_value=1,
    max_value=3,
    value=2,
)

use_llm = st.checkbox(
    "Use local Ollama model for root-cause analysis",
    value=False,
    help=(
        "Optional: uses a local language model. "
        "Keep disabled to minimize CPU and memory usage."
    ),
)

current_settings = {
    "example_name": example_name,
    "simulate_inconclusive": simulate_inconclusive,
    "max_retries": max_retries,
    "use_llm": use_llm,
}

settings_key = hashlib.sha256(
    repr(current_settings).encode("utf-8")
).hexdigest()

if st.session_state.get("investigation_settings_key") != settings_key:
    st.session_state.pop("investigation_result", None)
    st.session_state["investigation_settings_key"] = settings_key

if st.button("Investigate Failure", type="primary"):
    initial_state = {
        "example_name": example_name,
        "description": example["description"],
        "buggy_code": example["buggy_code"],
        "agent_trace": [],
        "retry_count": 0,
        "max_retries": max_retries,
        "simulate_inconclusive": simulate_inconclusive,
        "use_llm": use_llm,
    }

    try:
        with st.spinner("Agents are investigating the failure..."):
            workflow = build_workflow()
            result = workflow.invoke(initial_state)

        st.session_state["investigation_result"] = result

    except Exception as error:
        st.error(
            f"The investigation could not be completed: {error}"
        )

result = st.session_state.get("investigation_result")

if result:
    st.divider()
    st.markdown("## Investigation results")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Failure type",
        result.get("failure_type", "Unknown"),
    )

    col2.metric(
        "Priority",
        result.get("priority", "Unknown"),
    )

    col3.metric(
        "Retries used",
        result.get("retry_count", 0),
    )

    st.markdown("### Agent execution trace")

    for index, event in enumerate(
        result.get("agent_trace", []), start=1
    ):
        st.write(f"{index}. {event}")

    st.markdown("### Root-cause hypothesis")
    st.write(result.get("hypothesis", "Not available"))

    st.markdown("### Selected diagnostic test")
    st.write(result.get("selected_test", "Not available"))

    st.markdown("### Observed result")
    st.code(result.get("test_output", "No output"))

    st.subheader("MCP Diagnostic Evidence")

    mcp_result = result.get("mcp_result", {})

    if result.get("mcp_used", False):
        st.json(mcp_result)
    else:
        st.info(
            "No MCP diagnostic result was available for this attempt."
        )

    st.markdown("### Validation outcome")
    st.write(result.get("validation_status", "Not available"))

    if result.get("needs_human_review", True):
        st.warning(
            "Human review is required. Do not accept the diagnosis "
            "or modify code automatically."
        )
    else:
        st.success(
            "The observed result supports the current diagnosis. "
            "Review the proposed fix and run regression tests."
        )

    st.divider()
    st.subheader("Proposed Fix")

    if result.get("fix_available", False):
        st.info(
            "The following correction is a recommendation only. "
            "No project source files have been modified."
        )

        st.code(
            result.get("proposed_fix", ""),
            language="python",
        )

        st.warning(
            "Review the proposed correction before approving "
            "the predefined regression tests."
        )

        if result.get("regression_results"):
            st.subheader("Regression Test Results")

            st.write(result.get("regression_summary", ""))

            for index, test in enumerate(
                result["regression_results"], start=1
            ):
                passed = test.get("passed", False)

                if passed:
                    st.success(f"Test {index}: Passed")
                else:
                    st.error(f"Test {index}: Failed")

                st.json(test)

            if result.get("regression_passed", False):
                st.success(
                    "All regression tests passed against the "
                    "predefined corrected functions."
                )
            else:
                st.warning(
                    "Some regression tests failed or could not complete. "
                    "Review the evidence before proceeding."
                )

        elif not result.get("fix_approved", False):
            approval_confirmed = st.checkbox(
                "I have reviewed the proposed fix and approve "
                "running the predefined regression tests.",
                key="approve_testpilot_regression",
            )

            if st.button(
                "Approve Fix and Run Regression Tests",
                type="primary",
                disabled=not approval_confirmed,
            ):
                approved_state = dict(result)
                approved_state["fix_approved"] = True

                try:
                    with st.spinner(
                        "Running predefined regression tests..."
                    ):
                        regression_result = regression_testing_agent(
                            approved_state
                        )

                    result.update(regression_result)
                    result["fix_approved"] = True
                    st.session_state["investigation_result"] = result

                    st.rerun()

                except Exception as error:
                    st.error(
                        f"Regression testing failed: "
                        f"{type(error).__name__}: {error}"
                    )

        else:
            st.info(
                "Regression testing has been approved. "
                "Check the results above."
            )

    elif result.get("needs_human_review", False):
        st.warning(
            "A fix cannot be recommended until a human reviews "
            "the inconclusive investigation."
        )

    else:
        st.info(
            "No predefined fix is available for this investigation."
        )

    st.divider()
    st.markdown("### Final Investigation Report")

    if result.get("regression_results"):
        if result.get("regression_passed", False):
            result["next_action"] = (
                "The diagnosis is validated and all regression tests passed. "
                "Review the results; no original source code was modified."
            )
        else:
            result["next_action"] = (
                "Regression testing did not fully pass. Review the failed "
                "tests and investigate before accepting the recommendation."
            )
    elif result.get("fix_available", False):
        result["next_action"] = (
            "Review the proposed fix and approve the predefined regression "
            "tests when you are ready."
        )

    final_report = build_final_investigation_report(result)

    st.text(final_report)

    st.download_button(
        label="Download Investigation Report",
        data=final_report,
        file_name="testpilot_investigation_report.txt",
        mime="text/plain",
        key="download_final_investigation_report",
    )

st.divider()

st.caption(
    "TestPilot AI | Local proof of concept | "
    "No automatic code patches are applied."
)