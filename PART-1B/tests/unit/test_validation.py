from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from reminder_agent.models import ResolutionContext
from reminder_agent.validation import (
    InputValidationError,
    match_reminder_target,
    response_properties_valid,
    validate_context,
    validate_request_text,
)


def test_request_length_boundaries() -> None:
    validate_request_text("x" * 4096)
    with pytest.raises(InputValidationError):
        validate_request_text("x" * 4097)
    with pytest.raises(InputValidationError):
        validate_request_text("   ")


def test_context_requires_aware_reference_time_when_needed() -> None:
    context = ResolutionContext(
        reference_time=datetime(2026, 11, 19, 9, 0),
        timezone="Asia/Kolkata",
    )
    with pytest.raises(InputValidationError):
        validate_context(context, requires_reference=True)


def test_context_rejects_unknown_iana_timezone() -> None:
    context = ResolutionContext(
        reference_time=datetime(2026, 11, 19, 9, 0, tzinfo=ZoneInfo("UTC")),
        timezone="Not/A_Zone",
    )
    with pytest.raises(InputValidationError):
        validate_context(context, requires_reference=True)


def test_context_accepts_valid_aware_reference_time(context: ResolutionContext) -> None:
    validate_context(context, requires_reference=True)


def test_target_matching_requires_one_candidate() -> None:
    candidates = ("pay electricity bill", "attend project review")
    assert match_reminder_target("electricity bill", candidates) == "pay electricity bill"
    assert match_reminder_target("project review", candidates) == "attend project review"
    assert match_reminder_target("travel", candidates) is None


def test_target_matching_does_not_choose_between_multiple_candidates() -> None:
    candidates = ("pay electricity bill", "pay water bill")
    assert match_reminder_target("pay bill", candidates) is None


def test_context_validates_optional_values_when_not_required() -> None:
    validate_context(ResolutionContext(), requires_reference=False)

    with pytest.raises(InputValidationError, match="REFERENCE_TIME_INVALID"):
        validate_context(
            ResolutionContext(reference_time="not a datetime"),  # type: ignore[arg-type]
            requires_reference=False,
        )
    with pytest.raises(InputValidationError, match="TIMEZONE_INVALID"):
        validate_context(ResolutionContext(timezone=""), requires_reference=False)
    with pytest.raises(InputValidationError, match="REFERENCE_TIME_MISSING"):
        validate_context(
            ResolutionContext(timezone="UTC"),
            requires_reference=True,
        )
    with pytest.raises(InputValidationError, match="REMINDER_TASK_INVALID"):
        validate_context(
            ResolutionContext(reminder_tasks=("   ",)),
            requires_reference=False,
        )
    with pytest.raises(InputValidationError, match="REMINDER_TASK_INVALID"):
        validate_context(
            ResolutionContext(reminder_tasks=(7,)),  # type: ignore[arg-type]
            requires_reference=False,
        )


def test_target_matching_rejects_empty_or_nonmatching_tokens() -> None:
    assert match_reminder_target("!!!", ("pay electricity",)) is None
    assert match_reminder_target("electricity", ("!!!",)) is None
    assert match_reminder_target("travel", ("pay electricity",)) is None


def test_response_properties_accept_valid_action_and_clarification() -> None:
    action = {
        "intent": "create",
        "task": "pay bill",
        "datetime": "2026-11-20T18:00:00+05:30",
        "needs_clarification": False,
        "clarification_question": "",
    }
    clarification = {
        "intent": "clarification",
        "task": "",
        "datetime": "",
        "needs_clarification": True,
        "clarification_question": "When should I remind you?",
    }

    assert response_properties_valid(action)
    assert response_properties_valid(clarification)


@pytest.mark.parametrize(
    "response",
    [
        None,
        {},
        {"intent": "create", "extra": True},
        {
            "intent": "clarification",
            "task": "",
            "datetime": "",
            "needs_clarification": True,
            "clarification_question": " ",
        },
        {
            "intent": "create",
            "task": "pay bill",
            "datetime": "2026-11-20T18:00:00",
            "needs_clarification": False,
            "clarification_question": "",
        },
        {
            "intent": "create",
            "task": "",
            "datetime": "invalid",
            "needs_clarification": False,
            "clarification_question": "",
        },
        {
            "intent": "clarification",
            "task": "",
            "datetime": "",
            "needs_clarification": False,
            "clarification_question": "",
        },
    ],
)
def test_response_properties_reject_invalid_shapes_and_invariants(
    response: object,
) -> None:
    assert not response_properties_valid(response)
