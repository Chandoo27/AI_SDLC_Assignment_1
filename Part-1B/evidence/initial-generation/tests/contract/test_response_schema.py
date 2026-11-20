import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = (
    Path(__file__).parents[2]
    / "specs"
    / "001-reminder-agent"
    / "contracts"
    / "reminder-response.schema.json"
)


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.mark.parametrize(
    "response",
    [
        {
            "intent": "create",
            "task": "pay electricity bill",
            "datetime": "2026-11-20T18:00:00+05:30",
            "needs_clarification": False,
            "clarification_question": "",
        },
        {
            "intent": "reschedule",
            "task": "pay electricity bill",
            "datetime": "2026-11-21T18:00:00+05:30",
            "needs_clarification": False,
            "clarification_question": "",
        },
        {
            "intent": "snooze",
            "task": "pay electricity bill",
            "datetime": "2026-11-19T09:30:00+05:30",
            "needs_clarification": False,
            "clarification_question": "",
        },
        {
            "intent": "clarification",
            "task": "",
            "datetime": "",
            "needs_clarification": True,
            "clarification_question": "What task should I remind you about?",
        },
    ],
)
def test_valid_action_and_clarification_responses_pass_schema(
    validator: Draft202012Validator, response: dict[str, object]
) -> None:
    assert validator.is_valid(response)


@pytest.mark.parametrize(
    "response",
    [
        {},
        {
            "intent": "create",
            "task": "task",
            "datetime": "2026-11-20T18:00:00+05:30",
            "needs_clarification": False,
            "clarification_question": "",
            "extra": True,
        },
        {
            "intent": "create",
            "task": "task",
            "datetime": "not-a-date",
            "needs_clarification": False,
            "clarification_question": "",
        },
        {
            "intent": "clarification",
            "task": "",
            "datetime": "",
            "needs_clarification": True,
            "clarification_question": "",
        },
        {
            "intent": "create",
            "task": "",
            "datetime": "",
            "needs_clarification": False,
            "clarification_question": "",
        },
    ],
)
def test_invalid_responses_fail_schema(
    validator: Draft202012Validator, response: dict[str, object]
) -> None:
    assert not validator.is_valid(response)


def test_schema_has_exactly_the_five_public_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert set(schema["required"]) == {
        "intent",
        "task",
        "datetime",
        "needs_clarification",
        "clarification_question",
    }
    assert schema["additionalProperties"] is False
