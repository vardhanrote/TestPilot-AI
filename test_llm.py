
from testpilot.llm import generate_root_cause


def test_ollama_returns_a_root_cause_hypothesis():
    hypothesis = generate_root_cause(
        example_name="Empty List Bug",
        description=(
            "A function tries to return the first item "
            "without checking whether the list is empty."
        ),
        buggy_code=(
            "def get_first_item(items):\n"
            "    return items[0]"
        ),
    )

    assert isinstance(hypothesis, str)
    assert len(hypothesis.strip()) > 0

    print("\nOllama hypothesis:")
    print(hypothesis)


if __name__ == "__main__":
    test_ollama_returns_a_root_cause_hypothesis()
