from datetime import datetime
from zoneinfo import ZoneInfo

from reminder_agent.engine import process_request
from reminder_agent.models import ResolutionContext


def test_reschedule_matches_unique_target_and_replacement_time() -> None:
    context = ResolutionContext(
        reference_time=datetime(2026, 11, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        timezone="Asia/Kolkata",
        reminder_tasks=("pay electricity bill", "attend project review"),
    )

    response = process_request(
        "Reschedule pay electricity bill to tomorrow at 6 PM.",
        context,
    )

    assert response["intent"] == "reschedule"
    assert response["task"] == "pay electricity bill"
    assert response["datetime"] == "2026-11-20T18:00:00+05:30"


def test_ambiguous_target_requests_clarification() -> None:
    context = ResolutionContext(
        reference_time=datetime(2026, 11, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        timezone="Asia/Kolkata",
        reminder_tasks=("pay electricity bill", "pay water bill"),
    )

    response = process_request("Reschedule pay bill to tomorrow at 6 PM.", context)

    assert response["intent"] == "clarification"
    assert response["needs_clarification"] is True
    assert "reminder" in response["clarification_question"].lower()


def test_snooze_duration_is_relative_to_fixed_aware_reference() -> None:
    context = ResolutionContext(
        reference_time=datetime(2026, 11, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        timezone="Asia/Kolkata",
        reminder_tasks=("pay electricity bill",),
    )

    response = process_request("Snooze pay electricity bill for 30 minutes.", context)

    assert response["intent"] == "snooze"
    assert response["task"] == "pay electricity bill"
    assert response["datetime"] == "2026-11-19T09:30:00+05:30"
