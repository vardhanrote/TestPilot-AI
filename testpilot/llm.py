
import os
import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:1.5b",
)

OLLAMA_TIMEOUT_SECONDS = 35


def generate_root_cause(
    example_name: str,
    description: str,
    buggy_code: str,
) -> str:
    """
    Ask a local Ollama model to suggest a likely root cause.

    This function only analyzes the supplied text.
    It does not execute the supplied source code.
    """

    prompt = f"""
You are the Root-Cause Agent in TestPilot AI.

Analyze this synthetic software test failure.

Scenario:
{example_name}

Problem description:
{description}

Faulty source code (for analysis only):
{buggy_code}

Instructions:
1. Identify the most likely reason for the failure.
2. Explain the relevant condition or operation.
3. Recommend what a developer should inspect.
4. Do not claim that a test was executed.
5. Do not claim that your hypothesis has been validated.
6. Do not provide a long answer.

Return only a concise root-cause hypothesis in 2 to 4 sentences.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 120,
            "num_ctx": 1024,
        },
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    result = response.json()
    hypothesis = result.get("response", "").strip()

    if not hypothesis:
        raise ValueError(
            "Ollama returned an empty root-cause hypothesis."
        )

    return hypothesis
