# TestPilot AI

### An Agentic AI System for Automated Test Failure Investigation and Validation

TestPilot AI is a lightweight, agent-based system that investigates predefined software test failures, develops root-cause hypotheses, validates them using controlled diagnostic tools, recommends possible fixes, and runs regression tests after human approval.

The project combines **LangGraph, Ollama, Model Context Protocol (MCP), Python, and Streamlit** to demonstrate how agentic AI can assist with software testing and debugging.

> **Safety first:** TestPilot AI uses predefined synthetic examples and controlled diagnostic tools. It does not execute arbitrary uploaded source code or automatically modify the original source code.

## Table of Contents

- [Project Overview](#project-overview)
- [Objectives](#objectives)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [Example Scenarios](#example-scenarios)
- [Safety and Human Approval](#safety-and-human-approval)
- [Running Tests](#running-tests)
- [Current Limitations](#current-limitations)
- [Future Improvements](#future-improvements)

## Project Overview

Software test failures can require developers to inspect error messages, identify likely causes, reproduce the problem, and check whether a proposed correction introduces new issues.

TestPilot AI demonstrates a structured workflow for assisting with these activities. Instead of relying on a single AI response, the system uses specialized agents that perform different investigation tasks.

The system can use a local Ollama language model to generate a root-cause hypothesis. If the model is unavailable or produces an unusable response, a rule-based fallback provides a basic explanation.

Diagnostic evidence is collected through predefined MCP tools. After validation, the system can recommend a predefined correction. Regression tests run only after the user explicitly approves them.

## Objectives

1. Classify predefined software failures.
2. Generate understandable root-cause hypotheses.
3. Use controlled diagnostic tools to collect evidence.
4. Validate hypotheses against observed exceptions.
5. Retry an investigation when evidence is insufficient.
6. Recommend a predefined correction after successful validation.
7. Require human approval before regression testing.
8. Produce a consolidated investigation report.

## Features

- **Agent-based investigation:** Separates triage, root-cause analysis, test selection, experimentation, and validation.
- **Local LLM support:** Uses Ollama for root-cause hypothesis generation.
- **Rule-based fallback:** Allows basic analysis when Ollama is unavailable.
- **MCP diagnostics:** Uses predefined tools to inspect synthetic examples and reproduce expected exceptions.
- **Retry and escalation:** Repeats inconclusive investigations up to the configured limit and escalates when necessary.
- **Fix recommendations:** Displays predefined corrections without applying them to the original source code.
- **Human-approved regression testing:** Prevents regression tests from running unless approval and other safety conditions are satisfied.
- **Investigation reports:** Presents diagnostic evidence, validation status, proposed fixes, regression results, and recommended next steps.
- **Streamlit interface:** Provides an interactive interface for running and reviewing investigations.

## System Architecture

```text
                 User
                  |
                  v
             Streamlit UI
                  |
                  v
          LangGraph Workflow
                  |
                  v
             Triage Agent
                  |
                  v
          Root-Cause Agent
          /             \
         v               v
   Ollama LLM       Rule-Based Fallback
          \             /
                  |
                  v
        Test Selection Agent
                  |
                  v
          Experiment Agent
                  |
                  v
         Predefined MCP Tools
                  |
                  v
          Validation Agent
             /         \
       Retry needed   Validated
            |             |
            v             v
      Root-Cause     Fix Recommendation
        Agent              |
                           v
                   Human Approval
                           |
                           v
                  Regression Testing
                           |
                           v
                 Final Investigation
                        Report
```

The investigation workflow is orchestrated using LangGraph. The regression-testing stage is invoked separately by the application after approval; it is not an automatic source-code patching process.

### The five investigation agents

1. **Triage Agent:** Classifies the selected failure and assigns a priority.
2. **Root-Cause Agent:** Generates a hypothesis using Ollama or rule-based analysis.
3. **Test Selection Agent:** Selects the predefined diagnostic test for the scenario.
4. **Experiment Agent:** Calls an allowlisted MCP diagnostic tool and collects the result.
5. **Validation Agent:** Checks whether the evidence supports the hypothesis and decides whether to retry or escalate.

Additional workflow functions recommend predefined fixes, run approved regression tests, and prepare the final report.

## Technology Stack

| Technology | Purpose                                              |
| ---------- | ---------------------------------------------------- |
| Python     | Main programming language                            |
| Streamlit  | User interface                                       |
| LangGraph  | Agent workflow orchestration                         |
| Ollama     | Local language-model inference                       |
| MCP        | Controlled access to diagnostic and regression tools |
| Pytest     | Automated testing                                    |

## Project Structure

```text
TestPilot-AI/
├── app.py
├── requirements.txt
├── test_llm.py
├── testpilot/
│   ├── __init__.py
│   ├── examples.py
│   ├── state.py
│   ├── workflow.py
│   ├── llm.py
│   └── mcp_client.py
├── mcp_tools/
│   ├── __init__.py
│   └── server.py
└── tests/
    ├── test_examples.py
    ├── test_workflow.py
    └── test_mcp_tools.py
```

- `app.py`: Streamlit application.
- `testpilot/examples.py`: Predefined failure scenarios, proposed fixes, and regression cases.
- `testpilot/state.py`: Shared state used during an investigation.
- `testpilot/workflow.py`: Investigation agents, routing, validation, fix recommendations, regression testing, and report generation.
- `testpilot/llm.py`: Ollama integration.
- `testpilot/mcp_client.py`: MCP client and tool allowlist.
- `mcp_tools/server.py`: Predefined diagnostic and regression tools.
- `tests/`: Automated tests for examples, MCP tools, and workflow behaviour.
- `test_llm.py`: Test for the Ollama root-cause integration.

## Installation and Setup

### Prerequisites

- Windows 10 or Windows 11
- Python 3.11
- Git (optional, for version control)
- Ollama (optional; required for local LLM-based analysis)

### 1. Open the project folder

Open PowerShell or the VS Code terminal:

```powershell
cd C:\Users\ADMIN\TestPilot-AI
```

### 2. Create and activate a virtual environment

If the project already has a working `.venv`, activate it rather than creating another one.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the following in the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Use the project's existing dependency constraints in `requirements.txt`. The MCP SDK should remain on the compatible 1.x release range used by this project.

### 4. Optional: Configure Ollama

Install Ollama from its official website: https://ollama.com/

Download a small model suitable for CPU-based execution. For example:

```powershell
ollama pull qwen2.5:1.5b
```

Confirm that the model is available:

```powershell
ollama list
```

The model configured in the application must match the model downloaded locally. The application should be able to use its rule-based fallback when LLM analysis is disabled or unavailable.

## Running the Application

Activate the virtual environment and move to the project root:

```powershell
cd C:\Users\ADMIN\TestPilot-AI
.\.venv\Scripts\Activate.ps1
```

Start the Streamlit application:

```powershell
python -m streamlit run app.py
```

Streamlit will display a local URL in the terminal. Open that URL in your browser to use the application.

Choose a supported scenario, configure the available investigation settings, and start the investigation. Review the diagnostic evidence and proposed correction. Approve regression testing only when you are ready.

## Example Scenarios

### 1. Empty List Bug

The synthetic function attempts to access the first element of an empty list.

**Expected diagnostic result:** `IndexError`

**Proposed correction:** Check whether the list is empty before accessing its first element.

**Regression checks:** Confirm that an empty list returns `None` and that a non-empty list returns its first element.

### 2. Division by Zero

The synthetic function divides a numerator by a denominator without first checking whether the denominator is zero.

**Expected diagnostic result:** `ZeroDivisionError`

**Proposed correction:** Check the denominator and raise `ValueError` when it is zero.

**Regression checks:** Confirm that a zero denominator raises `ValueError` and that ordinary division still returns the expected result.

These examples demonstrate the investigation process. They do not represent automatic debugging of arbitrary files in a user's project.

## Safety and Human Approval

TestPilot AI follows a controlled approach to debugging:

- Diagnostic tools are predefined and allowlisted.
- The experiment agent does not execute arbitrary uploaded code.
- Diagnostic evidence must match the expected scenario before a fix is recommended.
- Inconclusive evidence can trigger a retry or human review.
- A proposed fix is a recommendation; it does not modify the original source file.
- Regression tests are blocked unless human approval is recorded and the required validation and fix conditions are satisfied.
- Regression tests use predefined corrected functions and test cases.

Passing regression tests means that the predefined regression cases passed. It does not prove that an original external codebase has been patched or is free of defects.

## Running Tests

Run the full automated test suite from the project root:

```powershell
python -m pytest -v
```

To run a specific test group:

```powershell
python -m pytest tests/test_examples.py -v
python -m pytest tests/test_mcp_tools.py -v
python -m pytest tests/test_workflow.py -v
```

The project has previously passed **18 automated tests** covering example definitions, MCP diagnostics, regression tools, successful diagnoses, retry and escalation behaviour, and approval checks.

Test results may change when the code or dependencies change. Run the suite again after making modifications.

## Current Limitations

- Only predefined synthetic failure scenarios are supported.
- The system does not autonomously inspect or execute arbitrary user repositories.
- Fix recommendations are predefined rather than generated and applied as source-code patches.
- Regression tests run against controlled corrected functions rather than an automatically modified original project.
- Root-cause quality depends on the local model when Ollama is enabled.
- The system demonstrates a controlled investigation workflow; it is not a replacement for a complete production-grade testing platform.

## Future Improvements

- Add more predefined failure scenarios and diagnostic tools.
- Integrate repository-aware static analysis without executing untrusted code.
- Add structured evidence scoring and richer validation rules.
- Improve investigation history and report export.
- Add more regression scenarios and configurable test suites.
- Evaluate additional lightweight local language models.

## Conclusion

TestPilot AI demonstrates how multiple specialized agents can cooperate to investigate software test failures, validate evidence, recommend corrections, and support regression testing under human supervision.

By combining LangGraph, local LLM inference, MCP tools, and a Streamlit interface, the project provides a practical foundation for exploring agentic AI in software testing.

---

**Project:** TestPilot AI  
**Title:** An Agentic AI System for Automated Test Failure Investigation and Validation
