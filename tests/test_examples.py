
from testpilot.examples import EXAMPLES


def test_empty_list_example_contains_expected_details():
    example = EXAMPLES["Empty List Bug"]

    assert "get_first_item" in example["buggy_code"]
    assert example["expected_exception"] == "IndexError"
    assert "list is empty" in example["description"]
