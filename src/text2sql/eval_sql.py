"""
Text2SQL correctness eval — M8 gate.
Checks: parameterisation, structure, expected keywords.
Pass rate must be ≥ 90% (at least 4/5) to clear the CI gate.
"""
import sys
from queries import SQL_QUERIES

TESTS = [
    {
        "id": "q1",
        "description": "Count signups for Chess Club",
        "must_contain": ["COUNT", "signups", "activities"],
        "must_not_contain": ["f\"", "f'", "% name", "+ name"],
        "must_use_params": True,
    },
    {
        "id": "q2",
        "description": "Activities with available spots",
        "must_contain": ["max_participants", "signups"],
        "must_not_contain": ["f\"", "f'"],
        "must_use_params": False,  # no user input in this query
    },
    {
        "id": "q3",
        "description": "Activities for a named student",
        "must_contain": ["signups", "activities", "student_name"],
        "must_not_contain": ["f\"", "f'", "+ student"],
        "must_use_params": True,
    },
    {
        "id": "q4",
        "description": "Activities with max_participants > 10",
        "must_contain": ["max_participants"],
        "must_not_contain": ["f\"", "f'"],
        "must_use_params": False,
    },
    {
        "id": "q5",
        "description": "Remove a student from an activity (DELETE)",
        "must_contain": ["DELETE", "signups", "student_name"],
        "must_not_contain": ["f\"", "f'", "+ student", "DROP"],
        "must_use_params": True,
    },
]


def run_eval():
    passed = 0
    for test in TESTS:
        qid = test["id"]
        entry = SQL_QUERIES.get(qid, {})
        sql = entry.get("sql", "")
        params = entry.get("params", None)

        failures = []

        for keyword in test["must_contain"]:
            if keyword.upper() not in sql.upper():
                failures.append(f"Missing keyword: {keyword}")

        for forbidden in test["must_not_contain"]:
            if forbidden in sql:
                failures.append(f"Forbidden pattern found: {forbidden}")

        if test["must_use_params"] and not params:
            failures.append("Parameterised query required but params tuple is empty/None")

        if failures:
            print(f"  FAIL [{qid}] {test['description']}")
            for f in failures:
                print(f"       → {f}")
        else:
            print(f"  PASS [{qid}] {test['description']}")
            passed += 1

    rate = passed / len(TESTS) * 100
    print(f"\nSQL correctness: {rate:.0f}% ({passed}/{len(TESTS)})")

    if rate < 90:
        print("BLOCKED: SQL correctness below 90% threshold.")
        sys.exit(1)
    print("PASSED: SQL correctness gate cleared.")


if __name__ == "__main__":
    run_eval()