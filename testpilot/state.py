from typing import TypedDict


class InvestigationState(TypedDict, total=False):
    # Selected debugging case
    example_name: str
    description: str
    buggy_code: str

    use_llm: bool

    # MCP diagnostic evidence
    mcp_result: dict
    mcp_used: bool

    # Triage findings
    failure_type: str
    priority: str

    # Investigation findings
    hypothesis: str
    selected_test: str
    test_output: str
    test_passed: bool

    # Decision-making
    validation_status: str
    retry_count: int
    max_retries: int
    simulate_inconclusive: bool

    # Fix recommendation
    proposed_fix: str
    fix_available: bool
    fix_approved: bool

    # Regression testing
    regression_results: list[dict]
    regression_passed: bool
    regression_summary: str

    # Final result
    final_report: str
    next_action: str
    needs_human_review: bool

    # Audit trail
    agent_trace: list[str]

