EXAMPLES = {
    "Empty List Bug": {
        "description": (
            "A function tries to return the first item "
            "without checking whether the list is empty."
        ),
        "buggy_code": (
            "def get_first_item(items):\n"
            "    return items[0]\n"
        ),
        "input_description": "An empty list: []",
        "expected_exception": "IndexError",
        "expected_root_cause": (
            "The function accesses index 0 without "
            "checking whether the list contains an item."
        ),
        "diagnostic_test": (
            "Call get_first_item([]) and examine "
            "the resulting behaviour."
        ),

        # Proposed correction shown to the user.
        # The original faulty code remains unchanged.
        "proposed_fix": (
            "def get_first_item(items):\n"
            "    if not items:\n"
            "        return None\n"
            "    return items[0]\n"
        ),

        # Expected behaviour after the proposed correction.
        "regression_tests": [
            {
                "name": "Empty list returns None",
                "input": [],
                "expected_result": None,
                "expected_exception": None,
            },
            {
                "name": "Non-empty list returns first item",
                "input": [10, 20, 30],
                "expected_result": 10,
                "expected_exception": None,
            },
        ],
    },

    "Division by Zero": {
        "description": (
            "A function divides one number by another "
            "without checking whether the denominator is zero."
        ),
        "buggy_code": (
            "def divide_numbers(numerator, denominator):\n"
            "    return numerator / denominator\n"
        ),
        "input_description": (
            "Numerator = 10, denominator = 0"
        ),
        "expected_exception": "ZeroDivisionError",
        "expected_root_cause": (
            "The function attempts to divide by zero "
            "without validating the denominator."
        ),
        "diagnostic_test": (
            "Call divide_numbers(10, 0) and examine "
            "the resulting behaviour."
        ),

        # Proposed correction shown to the user.
        # The original faulty code remains unchanged.
        "proposed_fix": (
            "def divide_numbers(numerator, denominator):\n"
            "    if denominator == 0:\n"
            "        raise ValueError('Denominator cannot be zero.')\n"
            "    return numerator / denominator\n"
        ),

        # Expected behaviour after the proposed correction.
        "regression_tests": [
            {
                "name": "Zero denominator is rejected",
                "input": {
                    "numerator": 10,
                    "denominator": 0,
                },
                "expected_result": None,
                "expected_exception": "ValueError",
            },
            {
                "name": "Normal division works",
                "input": {
                    "numerator": 10,
                    "denominator": 2,
                },
                "expected_result": 5.0,
                "expected_exception": None,
            },
        ],
    },
}

